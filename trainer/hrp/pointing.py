"""Run evalx's unmodified single-image cell, then normalize its journal."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

EVAL = Path('/scratch/jjyeung/orch_cd/evalx/work/aws_vl_pt')
RKIT = Path('/scratch/jjyeung/orch_cd/mdg_next/work/rkit')
MEMBERS = Path('/scratch/jjyeung/orch_cd/evalx/work/devpool/GROUND_MEMBERSHIP.json')
CHECKPOINTS = ('base', 't0m800', 'cp1m200')


def local_path(path):
    """Caller may name the local /scratch mount's path inside evalx's namespace."""
    root = Path(os.environ.get('HRP_LOCAL_ROOT', '/scratch')).resolve()
    if root == Path('/') or not root.is_absolute():
        raise ValueError('HRP_LOCAL_ROOT must name a specific local staging root')
    return Path(path).resolve().is_relative_to(root)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def kit(root=EVAL):
    sys.path.insert(0, str(Path(root) / 'evaluator'))
    import worker
    return worker


def prepare(out, checkpoint, max_pixels, video_root, pairs=None, membership=MEMBERS, eval_kit=EVAL):
    if max_pixels < 65536:
        raise ValueError('The evalx cell requires max_pixels >= 65536')
    if checkpoint not in CHECKPOINTS:
        raise ValueError('Unknown checkpoint')
    if not local_path(video_root):
        raise ValueError('Videos must already be under the local staging root (default /scratch)')
    source = json.loads(Path(membership).read_text())
    refs = {}
    for row in source['items']:
        if row['scene'] in refs and refs[row['scene']]['frame_indices'] != row['frame_indices']:
            raise ValueError('Conflicting anchor selections')
        refs[row['scene']] = row
    if pairs is None:
        sys.path.insert(0, str(RKIT))
        from rk.sets import scene_labels
        pairs = [dict(scene=s, obj=n) for s, names in scene_labels('dev').items() for n in names]
    pairs = sorted({(r['scene'], r['obj']) for r in pairs})
    out = Path(out).resolve()
    if (out/'config.json').exists():
        raise FileExistsError('Choose a fresh preparation directory; run resumes from an existing config')
    rows = []
    for scene, obj in pairs:
        ref = refs[scene]
        indices = ref['frame_indices']
        if len(indices) != 32 or indices != sorted(set(indices)):
            raise ValueError('Require 32 ordered, distinct source frames')
        for k, index in enumerate(indices, 1):
            rows.append({**{key: ref[key] for key in ('video_rel', 'fps', 'total_num_frames', 'frame_indices')},
                         'scene': scene, 'obj': obj, 'frame': k, 'source_index': index,
                         'id': digest([scene, obj, k])[:24]})
    write(out / 'membership.json', dict(grounding=True, contract=source['contract'], items=rows))
    pins = {n: sha(Path(eval_kit) / 'evaluator' / n) for n in
            ('worker.py', 'pointing.py', 'data.py', 'media.py', 'parity.py', 'scoring.py')}
    cfg = dict(cells=[dict(model=checkpoint, layout='spread', benchmarks=['pointing'],
                           decoding='greedy', image_max_pixels=max_pixels)],
               datasets=[dict(benchmark='pointing', membership=dict(path=str(out/'membership.json'),
                              sha256=sha(out/'membership.json')))],
               roots=dict(pointing_video_root=str(Path(video_root).resolve())),
               output=str(out/'journal'), max_model_len=8192, max_seqs=16, inflight=16,
               parity_per_benchmark=True, source_sha256=digest(pins), evalx_pins=pins)
    cfg['binding'] = digest(cfg)
    write(out / 'config.json', cfg)
    estimate = dict(questions=858 if pairs and len(pairs) == 589 else None,
                    pairs=len(pairs), scenes=len({s for s, _ in pairs}), generations=len(rows),
                    parity_generations=min(16, len(rows)), checkpoint=checkpoint, max_pixels=max_pixels,
                    assumed_generations_per_second=[1, 4],
                    estimated_gpu_minutes=[round(len(rows)/4/60+10), round(len(rows)/60+10)],
                    estimate_measured=False, note='One GPU; includes 10 minutes startup. Benchmark first 256 items.')
    write(out/'estimate.json', estimate)
    return estimate


def validate_pins(cfg, eval_kit):
    for name, expected in cfg['evalx_pins'].items():
        if sha(Path(eval_kit)/'evaluator'/name) != expected:
            raise ValueError('Evalx code changed; prepare a fresh bound run: '+name)


def run(config, model, cache, checkpoint, eval_kit=EVAL, rank=0, world=1):
    cfg = json.loads(Path(config).read_text())
    validate_pins(cfg, eval_kit)
    if checkpoint != cfg['cells'][0]['model']:
        raise ValueError('Checkpoint argument differs from the prepared cell')
    if not 0 <= rank < world:
        raise ValueError('Invalid rank/world')
    model = Path(model).resolve()
    if not local_path(model):
        raise ValueError('Model must already be under the local staging root (default /scratch)')
    identity = dict(path=str(model), config_sha256=sha(model/'config.json'), checkpoint=checkpoint)
    identity_file = Path(config).parent/'model_identity.json'
    if identity_file.exists() and json.loads(identity_file.read_text()) != identity:
        raise ValueError('Resume model identity differs')
    write(identity_file, identity)
    w = kit(eval_kit)
    args = SimpleNamespace(config=str(config), model=str(model), cache=str(cache), cell=0,
                           rank=rank, world=world, attempt='hrp', frames_sha256=sha(Path(cache)/'0.json'))
    asyncio.run(w.run(args))


def collect(config, out, eval_kit=EVAL):
    cfg = json.loads(Path(config).read_text())
    validate_pins(cfg, eval_kit)
    rows = json.loads(Path(cfg['datasets'][0]['membership']['path']).read_text())['items']
    journal_dir = Path(cfg['output'])/'0'
    complete = {}
    binding = digest_evalx(dict(request=cfg['binding'], cell=0), eval_kit)
    for path in sorted(journal_dir.glob('g*.jsonl')):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r['binding'] != binding:
                raise ValueError('Journal binding differs')
            complete[r['example_id']] = r
    checks = [c for p in sorted(journal_dir.glob('p*_hrp.json'))
              for c in json.loads(p.read_text())['checks']]
    expected = min(16, len(rows))
    check_ids = {c['example_id'] for c in checks}
    expected_ids = {r['id'] for r in sorted(rows, key=lambda r: r['id'])[:expected]}
    parity = (check_ids == expected_ids and len(checks) == expected
              and all(c.get('prompt_equal') and ('pixels' not in c or c['pixels'].get('pass')) for c in checks)
              and sum('pixels' in c for c in checks) == min(2, expected))
    sys.path.insert(0, str(Path(eval_kit)/'evaluator'))
    from pointing import parsed
    result = []
    for item in rows:
        r = complete.get(item['id'], {})
        raw = r.get('raw_generation')
        p = parsed(raw)
        status = ('missing' if not r else 'server_error' if r.get('status') != 'complete' else
                  'capped' if r.get('hit_token_cap') else 'invalid' if p['parse_failed'] else
                  'null' if p['none'] else 'multiple' if len(p['points']) != 1 else 'point')
        uv = p['points'][0] if status == 'point' else None
        meta = r.get('media', {}).get('metadata', {})
        h, w = meta.get('height'), meta.get('width')
        pixel = ([min(int(uv[0]/1000*w), w-1), min(int(uv[1]/1000*h), h-1)]
                 if uv is not None and h and w else None)
        result.append(dict(scene=item['scene'], obj=item['obj'], frame=item['frame'],
                           source_index=item['source_index'], frame_indices=item['frame_indices'],
                           raw_output=raw, point_2d=uv, point_pixel=pixel, source_hw=[h, w],
                           parse_status=status, checkpoint=cfg['cells'][0]['model'],
                           image_max_pixels=cfg['cells'][0]['image_max_pixels'], parity_pass=parity))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with Path(out).open('w') as f:
        for r in result:
            f.write(json.dumps(r, allow_nan=False)+'\n')
    summary = dict(expected=len(rows), completed=sum(r['parse_status'] not in ('missing', 'server_error') for r in result),
                   parity_pass=parity, cache=str(out), checkpoint=cfg['cells'][0]['model'])
    write(str(out)+'.summary.json', summary)
    return summary


def digest_evalx(value, eval_kit=EVAL):
    sys.path.insert(0, str(Path(eval_kit)/'evaluator'))
    from evalpath.items import digest as d
    return d(value)


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument('--eval-kit', type=Path, default=EVAL)
    sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('prepare')
    a.add_argument('--out', required=True)
    a.add_argument('--checkpoint', choices=CHECKPOINTS, required=True)
    a.add_argument('--max-pixels', type=int, required=True)
    a.add_argument('--video-root', required=True)
    a.add_argument('--pairs', help='JSON list of {scene, obj}; omitted means the 858-question dev set')
    a.add_argument('--membership', type=Path, default=MEMBERS)
    a = sub.add_parser('run')
    for key in ('config', 'model-dir', 'cache', 'checkpoint'):
        a.add_argument('--'+key, required=True)
    a.add_argument('--rank', type=int, default=0)
    a.add_argument('--world', type=int, default=1)
    a = sub.add_parser('collect')
    a.add_argument('--config', required=True)
    a.add_argument('--out', required=True)
    a = sub.add_parser('stage')
    a.add_argument('--config', required=True)
    a.add_argument('--cache', required=True)
    args = p.parse_args()
    if args.command == 'prepare':
        print(json.dumps(prepare(args.out, args.checkpoint, args.max_pixels, args.video_root,
                                json.loads(Path(args.pairs).read_text()) if args.pairs else None,
                                args.membership, args.eval_kit)))
    elif args.command == 'run':
        run(args.config, args.model_dir, args.cache, args.checkpoint, args.eval_kit, args.rank, args.world)
    elif args.command == 'stage':
        # Operator schedules this I/O separately; never decode on the inference worker.
        kit(args.eval_kit)
        from frame_stage import stage
        from data import tasks_for
        cfg = json.loads(Path(args.config).read_text())
        for spec in cfg['datasets']:
            for task in tasks_for(spec, cfg['roots']):
                if not Path(task['video_path']).resolve().is_relative_to('/scratch'):
                    raise ValueError('Refusing a video outside node-local /scratch')
        import av
        original_open = av.open
        def single_thread_open(*values, **kwargs):
            container = original_open(*values, **kwargs)
            for stream in container.streams.video:
                stream.thread_count = 1
            return container
        av.open = single_thread_open
        stage(args.config, args.cache, workers=1)
    else:
        summary = collect(args.config, args.out, args.eval_kit)
        print(json.dumps(summary))
        if not summary['parity_pass'] or summary['completed'] != summary['expected']:
            raise SystemExit(2)


if __name__ == '__main__':
    main()
