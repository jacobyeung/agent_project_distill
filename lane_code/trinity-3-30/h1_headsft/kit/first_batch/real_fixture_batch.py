"""CPU S1/S2 code-path diagnostic; fixture labels do not measure accuracy.

The only injectable seam is the model/processor loader. Rows.get, pixel loading,
packing, readout, faithful rendering, forward and backward are native paths.
"""
import argparse
from collections import Counter
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import resource
import sys
import time

K = Path(__file__).resolve().parents[1]


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', default=str(K/'configs/h1_1.json'))
    for name in ('model-manifest', 'receipt', 'artifact', 'frames', 'output'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--frames-root', help='Root for relative frame paths; absolute paths stay unchanged')
    p.add_argument('--ranks', default='0,1,2,3')
    p.add_argument('--routing-per-rank', type=int, default=2)
    p.add_argument('--force-pose-own', action='store_true')
    p.add_argument('--threads', type=int, default=16)
    return p


@contextmanager
def local_io(output):
    """Guard resolved paths, including symlinks; allow imports from K/tree."""
    active = True
    output = Path(output).resolve()

    def hook(event, args):
        if not active:
            return
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            part = path.parts[1] if len(path.parts) > 1 else ''
            if part in ('home', 'lustre') or part.startswith('data'):
                raise PermissionError('CPU fixture batch requires node-local staged inputs: '+str(path))
            mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if writing and not path.is_relative_to(output):
                raise PermissionError('Diagnostic writes must stay under --output: '+str(path))
        if event in ('socket.connect', 'socket.getaddrinfo', 'subprocess.Popen', 'os.remove', 'os.rmdir'):
            raise PermissionError('CPU fixture batch forbids network, subprocesses and deletions')
    sys.addaudithook(hook)
    try:
        yield
    finally:
        active = False


def read_inputs(args):
    from student_pilot.p3_provenance import file_pin
    from student_pilot.carrier_c1_sweep import recipe_for
    cfg = json.loads(Path(args.config).read_text())
    manifest = json.loads(Path(args.model_manifest).read_text())
    receipt = json.loads(Path(args.receipt).read_text())
    artifact = json.loads(Path(args.artifact).read_text())
    pin = file_pin(args.artifact)
    if pin['sha256'] != cfg['init_artifact']['artifact']['sha256']:
        raise ValueError('step-544 artifact digest differs from the D0 initialization pin')
    if artifact.get('step') != 544:
        raise ValueError('expected the step-544 initialization export')
    if manifest.get('schema') != 'p3-model-input-v1':
        raise ValueError('expected a p3-model-input-v1 model manifest')
    if cfg.get('training_mode') != 'final' or not all(cfg['h1'].get(k) for k in (
            'faithful_own_camera_rows', 'routing_pose_targets')):
        raise ValueError('fixture diagnostic requires final mode with S1 and S2')
    recipe = recipe_for(cfg)
    return cfg, manifest, {**receipt, 'recipe': recipe, 'h1': cfg['h1']}, pin


def real_loader(manifest, receipt, artifact_pin):
    from student_pilot import carrier_c1_run as R
    try:
        # Open a declared asset before Transformers can turn a missing directory
        # into a hub identifier. This is metadata-only until an actual run loads it.
        root = Path(manifest['root'])
        for name in manifest['files']:
            if Path(name).name != name:
                raise ValueError('model manifest asset must be a filename')
            with (root/name).open('rb'):
                pass
        processor = R.processor_for_receipt(manifest, receipt)
        loading = {k: v for k, v in receipt.items() if k not in ('init_artifact', 'depth_init')}
        model = R.load_model(manifest, loading, processor, evaluation=True)
        R.load_artifact(model, artifact_pin)
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise FileNotFoundError('Missing node-local model/processor/artifact file: '+str(exc)) from exc
    return model, processor


def fixture_rows(cfg, processor, frames, frames_root=None):
    from student_pilot import carrier_c1_run as R, carrier_c1_routing as routing
    from student_pilot.camera_targets import trajectory_scale
    import numpy as np

    clip = json.loads(Path(frames).read_text())
    if len(clip['frames']) != 32:
        raise ValueError('fixture clip must contain exactly 32 frames')
    indices = [f['source_index'] for f in clip['frames']]
    if any(type(i) is not int or i < 0 for i in indices) or indices != sorted(set(indices)):
        raise ValueError('clip source indices must be unique increasing nonnegative integers')
    if not math.isfinite(clip['fps']) or clip['fps'] <= 0 or clip['total_num_frames'] <= indices[-1]:
        raise ValueError('clip requires original positive fps and total_num_frames')
    root = Path(frames_root).resolve() if frames_root else Path(frames).resolve().parent
    for frame in clip['frames']:
        frame['path'] = str((root/Path(frame['path'])).resolve())
    packed, ground_skipped = [], []
    for name in ('camera_fixtures.jsonl', 'ground_fixtures.jsonl'):
        for line in (K/'rows'/name).read_text().splitlines():
            raw = json.loads(line)
            # Fixture programs refer to slots 1..32. Bind those slots to the real
            # clip's source indices; geometry/answers remain fixture diagnostics.
            raw['provenance']['frame_indices'] = indices
            try:
                packed.append(routing.c1_row(raw, clip))
            except ValueError as exc:
                if name != 'ground_fixtures.jsonl':
                    raise
                ground_skipped.append(dict(qid=raw['qid'], reason=str(exc)))
    if len(packed) + len(ground_skipped) != 14:
        raise ValueError('expected 12 camera and two optional a0 ground fixture rows')
    raw = packed[0]['routing']
    poses = np.asarray(raw['gt_pose9'], dtype=np.float32)
    pose_target = dict(camera=poses.tolist(), camera_mask=[True]*32,
                       trajectory_scale=float(trajectory_scale(poses, np.ones(32, dtype=bool))),
                       gravity=raw['gt_up'], gravity_mask=True,
                       point_depth=dict(uv=[[[500., 500.]]]*32, depth=[[1.]]*32, mask=[[False]]*32))

    class FixtureRows(R.Rows):
        def row(self, stream, index):
            if stream == 'routing':
                return routing.tool_mode(packed[index % len(packed)], self.tool_flag), None
            if stream == 'pose':
                return packed[0], pose_target
            raise ValueError('fixture diagnostic only materializes routing and pose')

    # Native initialization with no database connections. Only row retrieval is
    # replaced; Rows.get and all its encoders remain the trainer implementation.
    rows = FixtureRows({k: v for k, v in {**cfg, 'streams': {}}.items()
                        if k not in ('validation', 'mdg')}, processor)
    rows.counts = {s: len(packed) if s == 'routing' else 16 for s in set(cfg['mix'])}
    return rows, dict(camera=12, ground=len(packed)-12, ground_skipped=ground_skipped,
                      pose='fixture GT pose; depth labels masked',
                      frames=clip, fixture_geometry_matches_frames=False)


def run(args, loader=None):
    import torch
    from student_pilot import carrier_c1_run as R, carrier_c1_routing as routing
    from student_pilot.carrier_c1_data import mixed_indices
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('Set CUDA_VISIBLE_DEVICES="" for this CPU-only diagnostic')
    if not 1 <= args.threads <= 16:
        raise ValueError('--threads must be in 1..16')
    ranks = [int(r) for r in args.ranks.split(',')]
    if not ranks or len(set(ranks)) != len(ranks) or any(r not in range(4) for r in ranks):
        raise ValueError('--ranks must be distinct ranks in 0,1,2,3')
    if args.routing_per_rank < 1:
        raise ValueError('--routing-per-rank must be positive')
    torch.set_num_threads(args.threads)
    out = Path(args.output).resolve()
    root_part = out.parts[1] if len(out.parts) > 1 else ''
    if root_part in ('home', 'lustre') or root_part.startswith('data'):
        raise PermissionError('--output must be node-local: '+str(out))
    out.mkdir(parents=True, exist_ok=True)
    if any((out/n).exists() for n in ('SUMMARY.json', 'real_fixture_batch.jsonl')):
        raise ValueError('Use a fresh output directory; diagnostic records already exist')
    started = time.perf_counter()
    summary = dict(pass_flag=False, **{'pass': False}, step=2, force_pose_own=args.force_pose_own,
                   ranks={}, non_finite=[], errors=[], diagnostic_only=True,
                   distributed=False, weight_updates=0)
    rows = None
    with local_io(out):
        try:
            cfg, manifest, receipt, pin = read_inputs(args)
            model, processor = (loader or real_loader)(manifest, receipt, pin)
            model.recipe = receipt['recipe']
            model.to(torch.device('cpu')).train()
            rows, summary['fixtures'] = fixture_rows(cfg, processor, args.frames, args.frames_root)
            recipe = model.recipe
            counts = {s: rows.count(s) for s in set(recipe['mix'])}
            plan = next(mixed_indices(counts, 2, start_step=1, seed=17,
                                     training_mode='final', mix=recipe['mix'], world=4))
            summary.update(plan_counts=counts, hash_seed=os.environ.get('PYTHONHASHSEED'),
                           artifact=pin, plan=[dict(microstep=i, stream=s, indices=idx)
                                               for i, (s, idx) in enumerate(plan)])
            if sum(s == 'routing' for s, _ in plan) < args.routing_per_rank:
                raise ValueError('--routing-per-rank exceeds the step-2 routing plan')
            factor = recipe.get('reference_world_size', 4)//4
            gates = routing.Gates(recipe['scheduled_sampling'], getattr(model, 'depth_stage1', False))
            with (out/'real_fixture_batch.jsonl').open('x') as handle:
                for rank in ranks:
                    stat = dict(own=0, gt=0, refused=0, own_camera=0, routing=0, pose=0,
                                refusal_histogram={})
                    summary['ranks'][str(rank)] = stat
                    histogram = Counter()
                    for micro, (stream, indices) in enumerate(plan):
                        if stream == 'routing' and stat['routing'] < args.routing_per_rank:
                            pass
                        elif stream == 'pose' and stat['pose'] == 0:
                            pass
                        else:
                            continue
                        index = indices[rank]
                        begin = time.perf_counter()
                        batch, targets, audit = rows.get(stream, index)
                        R.check_row(batch, targets, stream, model)
                        encoded = time.perf_counter()
                        decision = None
                        if stream == 'routing':
                            decision = gates.decide(2, micro//factor)
                            if args.force_pose_own:
                                decision = (decision[0], True)
                            batch, audit = R.own_values(model, rows, batch, audit, index,
                                                       decision, torch.device('cpu'))
                        read = time.perf_counter()
                        model.zero_grad(set_to_none=True)
                        value = model(batch, targets, stream=stream)
                        forward = time.perf_counter()
                        finite_loss = bool(torch.isfinite(value['loss']).all())
                        bad_gradients = []
                        gradient_count = 0
                        if finite_loss:
                            value['loss'].backward()
                            backward = time.perf_counter()
                            for name, parameter in model.named_parameters():
                                if parameter.grad is not None:
                                    gradient_count += 1
                                    # Bound temporary memory for the 9B parameter scan.
                                    flat = parameter.grad.detach().reshape(-1)
                                    if any(not bool(torch.isfinite(chunk).all()) for chunk in flat.split(1048576)):
                                        bad_gradients.append(name)
                        else:
                            backward = forward
                        checked = time.perf_counter()
                        h1 = audit.get('h1', dict(type='pose', values='gt', refused=None, answer_differs=False))
                        stat[stream] += 1
                        if stream == 'routing':
                            stat[h1['values']] += 1
                            stat['own_camera'] += int(h1['values'] == 'own' and h1['type'] in routing.CAMERA_MOTION)
                            if h1['refused']:
                                stat['refused'] += 1
                                histogram[h1['refused']] += 1
                                stat['refusal_histogram'] = dict(histogram)
                        if not finite_loss or bad_gradients:
                            summary['non_finite'].append(dict(rank=rank, microstep=micro,
                                                             loss=not finite_loss, gradients=bad_gradients))
                        if gradient_count == 0:
                            summary['errors'].append(f'rank {rank} microstep {micro}: no gradients')
                        def number(v):
                            n = float(v.detach()) if isinstance(v, torch.Tensor) else float(v)
                            return n if math.isfinite(n) else None
                        record = dict(rank=rank, microstep=micro, stream=stream, step=2,
                                      force_pose_own=args.force_pose_own,
                                      planned_index=index, fixture_index=index % rows.count('routing') if stream == 'routing' else 0,
                                      decision=decision, h1=h1, audit=audit, loss=number(value['loss']),
                                      components={k: number(v) for k, v in value['components'].items()},
                                      finite_loss=finite_loss, finite_gradients=not bad_gradients,
                                      nonfinite_gradients=bad_gradients, gradient_tensors=gradient_count,
                                      trained_tokens=int((batch['labels'] != -100).sum()),
                                      seconds=dict(encode=encoded-begin, readout=read-encoded,
                                                   forward=forward-read, backward=backward-forward,
                                                   gradient_check=checked-backward, total=checked-begin),
                                      peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
                        line = json.dumps(record, allow_nan=False)
                        handle.write(line+'\n'); handle.flush()
                        print(line, flush=True)
                        del value, batch, targets
                        model.zero_grad(set_to_none=True)
            if args.force_pose_own:
                summary['errors'].extend(f'rank {rank}: no successful own camera row in selected routing microsteps'
                                         for rank, stat in summary['ranks'].items() if stat['own_camera'] == 0)
            summary['pass'] = (not summary['non_finite'] and not summary['errors'] and
                               all(s['routing'] == args.routing_per_rank and s['pose'] == 1 and
                                   (s['own_camera'] > 0 or not args.force_pose_own)
                                   for s in summary['ranks'].values()))
        except Exception as exc:
            summary['errors'].append(type(exc).__name__+': '+str(exc))
        finally:
            if rows is not None:
                rows.close()
            summary['pass_flag'] = summary['pass']
            summary['total_seconds'] = time.perf_counter()-started
            summary['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            (out/'SUMMARY.json').write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: v for k, v in summary.items() if k not in ('fixtures', 'plan')}), flush=True)
    return summary


def main(argv=None):
    args = parser().parse_args(argv)
    return 0 if run(args)['pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
