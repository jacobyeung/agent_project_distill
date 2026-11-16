"""Routed GH click-source journals and program-harness ground files."""
import argparse
from collections import defaultdict
import fcntl
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
import time

import torch

from .p3_provenance import digest, file_pin, load, pinned, write

EVALX = '/scratch/jjyeung/orch_cd/evalx/work/aws_vg/evaluator'


def pointing_module(root=None):
    root = Path(root or os.environ.get('GROUNDING_EVALX_ROOT', EVALX)).resolve()
    name = '_grounding_evalpath_' + digest(str(root))[:16]
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, root/'evalpath/__init__.py',
                                                    submodule_search_locations=[str(root/'evalpath')])
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return importlib.import_module(name+'.pointing_markers')


def tasks_for(membership, pm, video_root=None):
    root = Path(video_root or os.environ.get('GROUNDING_VIDEO_ROOT') or
                membership.get('roots', {}).get('pointing_video_root', pm.VIDEO_ROOT))
    tasks, seen = [], set()
    for row in membership['items']:
        name, indices, k = row['id'], row['frame_indices'], row['frame']
        if (not isinstance(name, str) or not name or name in seen or type(k) is not int or not 1 <= k <= 32
                or len(indices) != 32 or indices != sorted(indices)
                or indices[k-1] != row['source_index'] or not math.isfinite(row['fps']) or row['fps'] <= 0
                or any(type(i) is not int or not 0 <= i < row['total_num_frames'] for i in indices)):
            raise ValueError('Invalid pointing identity or source selection')
        seen.add(name)
        video = row.get('video_path') or str(root/Path(row['video_rel']).name)
        tasks.append(dict(benchmark='pointing_video', example_id=name+':A', membership_id=name,
            variant='A', scene=row['scene'], obj=row['obj'], frame=k, source_index=row['source_index'],
            source_frame_indices=indices, fps=row['fps'], total_num_frames=row['total_num_frames'],
            video_path=str(Path(video).resolve()), question=pm.QUESTION.format(obj=row['obj'], k=k), options=[]))
    return sorted(tasks, key=lambda t: t['example_id'])


def group_tasks(tasks, rank, world):
    if type(world) is not int or world < 1 or type(rank) is not int or not 0 <= rank < world:
        raise ValueError('Invalid rank/world')
    groups = defaultdict(list)
    for task in tasks:
        groups[(task['video_path'], tuple(task['source_frame_indices']))].append(task)
    ordered = sorted(groups)
    for key in ordered:
        if len({(t['fps'], t['total_num_frames']) for t in groups[key]}) != 1:
            raise ValueError('Conflicting clip metadata')
    return [sorted(groups[key], key=lambda t: t['example_id']) for key in ordered[rank::world]]


def artifact_pin(value):
    try:
        path, sha = value.rsplit('@', 1)
    except ValueError as exc:
        raise ValueError('Require artifact absolute-path@sha256') from exc
    pin = dict(path=path, sha256=sha)
    pinned(pin)
    return pin


def load_runtime(cfg, artifact, gh_dir, device):
    from .r2_policy import legacy_reader_guard
    legacy_reader_guard(cfg, artifact)
    from . import carrier_c1_run as run
    from .grounding_head import load_artifact
    receipt, manifest = run.prepared(cfg, admission=True)
    processor = run.processor_for_receipt(manifest, receipt)
    model = run.load_model(manifest, receipt, processor)
    loaded = run.load_artifact(model, artifact)
    if loaded['base_identity'] != cfg['base_identity']:
        raise ValueError('T0 base identity differs')
    gh, meta = load_artifact(gh_dir)
    if meta.get('base_artifact') != artifact:
        raise ValueError('GH was trained against another T0 artifact')
    if type(meta.get('tau')) not in (int, float) or not 0 <= meta['tau'] <= 1:
        raise ValueError('GH requires a frozen tau in [0,1]')
    model.to(device).eval().requires_grad_(False)
    model.grounding_head = gh.to(device).float().eval().requires_grad_(False)
    model.grounding_meta, model.grounding_tokenizer = meta, processor.tokenizer
    return model, processor


@torch.no_grad()
def predict_group(model, processor, cfg, tasks, frame_cache, pm, device):
    from .carrier_c1_canary import prompt_batch
    from .carrier_c1_decode import ground_predictions
    from .carrier_c1_run import move
    from .grounding_features import capture
    row, receipt = pm.trainer_row(tasks[0], frame_cache)
    batch = move(prompt_batch(processor, row, cfg), device)
    features = capture(model, batch)
    names = sorted({t['obj'] for t in tasks})
    outputs = ground_predictions(model, processor.tokenizer, model.grounding_head, features, names)
    patch = model.config.vision_config.patch_size * model.config.vision_config.spatial_merge_size
    audit = dict(processed_height_width=[features.grid[0]*patch, features.grid[1]*patch],
        trainer_prompt_ids_sha256=digest(batch['input_ids'][0].tolist()),
        anchor_pixel_sha256=receipt['anchor_pixel_sha256'], duplicate_pixel_sha256=receipt['duplicate_pixel_sha256'])
    return {o['name']: o for o in outputs}, audit


def record_for(task, output, tau, binding, rank, audit):
    k = task['frame'] - 1
    text = json.dumps(dict(point_2d=output['uv'][k] if output['prob'][k] >= tau else None))
    record = {key: task[key] for key in ('benchmark', 'example_id', 'membership_id', 'variant',
                                        'scene', 'obj', 'frame', 'source_index')}
    record.update(item_id=task['membership_id'], condition='markers_on', model='gh',
        key='pointing_video:'+task['example_id']+':markers_on', binding=binding, rank=rank,
        attempt='gh', status='complete', raw_generation=text, response_text=text, max_new_tokens=0,
        gh=dict(prob=output['prob'], uv=output['uv'], tau=tau), num_frames=64, num_viewpoints=32, **audit)
    return record


def read_journal(path, binding, expected, rank):
    records = {}
    if not path.exists():
        return records
    with path.open() as stream:
        for line in stream:
            row = json.loads(line)
            key = row['membership_id']
            task = expected.get(key)
            if (task is None or row.get('binding') != binding or row.get('rank') != rank
                    or row.get('condition') != 'markers_on' or row.get('model') != 'gh'
                    or any(row.get(k) != task[k] for k in ('example_id', 'scene', 'obj', 'frame', 'source_index'))):
                raise ValueError('Journal input identity or shard differs')
            if records.get(key, {}).get('status') == 'complete':
                raise ValueError('Duplicate completed item')
            records[key] = row
    return records


def save_equal(path, value):
    if path.exists():
        if load(path) != value:
            raise ValueError('Output identity differs: '+str(path))
    else:
        write(path, value)


def make_request(membership, gh, t0_config, artifact, frame_cache, world, pm):
    return dict(schema='grounding-eval-v1', membership=file_pin(membership), gh=str(Path(gh).resolve()),
        gh_meta=file_pin(Path(gh)/'gh.json'), gh_weights=file_pin(Path(gh)/'gh.pt'),
        t0_config=file_pin(t0_config), artifact=artifact, frame_cache=str(Path(frame_cache).resolve()),
        world=world, pointing_source=file_pin(pm.__file__), evalx_root=str(Path(pm.__file__).parents[1]),
        video_root=os.environ.get('GROUNDING_VIDEO_ROOT'))


def run_worker(membership, gh, t0_config, artifact, frame_cache, out, rank, world, *,
               evalx_root=None, device=None):
    pm = pointing_module(evalx_root)
    request = make_request(membership, gh, t0_config, artifact, frame_cache, world, pm)
    cfg = load(pinned(request['t0_config']))
    if (cfg.get('carrier_placement') != 'append_after_temporal_group_video_tokens_v1'
            or cfg.get('frame_layout') != 'duplicate' or cfg.get('frame_markers') is not True
            or cfg.get('training_mode') != 'final' or cfg.get('depth_enabled', True) is not True):
        raise ValueError('GH eval requires routed C1_A, duplicate frames, markers and private depth')
    tasks = tasks_for(load(pinned(request['membership'])), pm, request['video_root'])
    groups = group_tasks(tasks, rank, world)
    expected = {t['membership_id']: t for group in groups for t in group}
    output = Path(out)
    output.mkdir(parents=True, exist_ok=True)
    binding = digest(request)
    with (output/'binding.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        save_equal(output/'run.json', request)
    with (output/f'worker-{rank}.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        journal = output/f'items-{rank}.jsonl'
        records = read_journal(journal, binding, expected, rank)
        pending = [[t for t in group if records.get(t['membership_id'], {}).get('status') != 'complete']
                   for group in groups]
        pending = [group for group in pending if group]
        if pending:
            device = device or f'cuda:{rank}'
            model, processor = load_runtime(cfg, artifact, gh, device)
            for group in pending:
                started = time.perf_counter()
                try:
                    predictions, audit = predict_group(model, processor, cfg, group, frame_cache, pm, device)
                    rows = [record_for(t, predictions[t['obj']], model.grounding_meta['tau'], binding, rank, audit)
                            for t in group]
                except Exception as exc:
                    rows = []
                    for task in group:
                        row = record_for(task, dict(prob=[0.]*32, uv=[[0, 0]]*32), 1., binding, rank, {})
                        row.update(status='error', raw_generation='', response_text=None,
                                   error=f'{type(exc).__name__}: {exc}')
                        row.pop('gh')
                        rows.append(row)
                with journal.open('a') as stream:
                    for row in rows:
                        row['elapsed_s'] = time.perf_counter()-started
                        stream.write(json.dumps(row, sort_keys=True, allow_nan=False)+'\n')
                        stream.flush()
                        records[row['membership_id']] = row
        return dict(binding=binding, rank=rank, expected=len(expected),
                    completed=sum(r['status'] == 'complete' for r in records.values()))


def merge(out, world):
    output = Path(out)
    request = load(output/'run.json')
    if world != request['world']:
        raise ValueError('Merge world differs')
    for key in ('membership', 't0_config', 'artifact', 'gh_meta', 'gh_weights', 'pointing_source'):
        pinned(request[key])
    pm = pointing_module(request['evalx_root'])
    tasks = tasks_for(load(pinned(request['membership'])), pm, request['video_root'])
    binding, records = digest(request), {}
    for rank in range(world):
        expected = {t['membership_id']: t for group in group_tasks(tasks, rank, world) for t in group}
        rows = read_journal(output/f'items-{rank}.jsonl', binding, expected, rank)
        if set(rows) != set(expected) or any(r['status'] != 'complete' for r in rows.values()):
            raise ValueError('Missing or failed items; resume workers before merging')
        records.update(rows)
    text = ''.join(json.dumps(row, sort_keys=True, allow_nan=False)+'\n' for _, row in sorted(records.items()))
    path = output/'per-item.jsonl'
    if path.exists():
        if path.read_text() != text:
            raise ValueError('Merged records differ')
    else:
        with path.open('x') as stream:
            stream.write(text)
    summary = dict(binding=binding, expected_count=len(tasks), completed=len(records), coverage_complete=True,
        parity_pass=False, numbers_status='do not count', click_source='grounding_head',
        protocol_request=dict(preset='pointing_markers', kind='candidate', with_base=False,
                              candidates=[dict(name='gh', artifact=request['artifact'])]),
        models=dict(gh=dict(parity_pass=False)), membership_sha256=request['membership']['sha256'])
    save_equal(output/'summary.json', summary)
    return summary


def to_ground(records, membership, tag, out='out/ground'):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', tag):
        raise ValueError('Invalid ground tag')
    scenes = {r['id']: r['scene'] for r in load(membership)['items']}
    grouped, seen = defaultdict(dict), set()
    with Path(records).open() as stream:
        for line in stream:
            row = json.loads(line)
            item = row.get('membership_id', row.get('example_id', '').removesuffix(':A'))
            if item not in scenes or row.get('status', 'complete') != 'complete':
                continue
            if item in seen:
                raise ValueError('Duplicate ground item')
            seen.add(item)
            text = row.get('response_text', row.get('raw_generation'))
            if text is not None:
                grouped[scenes[item]][item] = text
    directory = Path(out)/('ground_'+tag)
    directory.mkdir(parents=True, exist_ok=False)
    for scene, values in sorted(grouped.items()):
        if not re.fullmatch(r'[A-Za-z0-9_/-]+', scene) or any(s in ('.', '..', '') for s in scene.split('/')):
            raise ValueError('Unsafe ground scene')
        write(directory/(scene.replace('/', '__')+'.json'), dict(scene=scene, out=values))
    return dict(output=str(directory), items=sum(map(len, grouped.values())), scenes=len(grouped))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    run = commands.add_parser('run')
    for name in ('membership', 'gh', 't0-config', 'artifact', 'frame-cache', 'out'):
        run.add_argument('--'+name, required=True)
    run.add_argument('--rank', required=True, type=int)
    run.add_argument('--world', required=True, type=int)
    run.add_argument('--evalx-root', default=None)
    combine = commands.add_parser('merge')
    combine.add_argument('--out', required=True)
    combine.add_argument('--world', required=True, type=int)
    ground = commands.add_parser('to-ground')
    for name in ('records', 'membership', 'tag'):
        ground.add_argument('--'+name, required=True)
    ground.add_argument('--out', default='out/ground')
    args = vars(parser.parse_args(argv))
    command = args.pop('command')
    if command == 'run':
        args['artifact'] = artifact_pin(args['artifact'])
        result = run_worker(**args)
    elif command == 'merge':
        result = merge(**args)
    else:
        result = to_ground(**args)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
