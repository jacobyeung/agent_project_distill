"""Export MDG masks and C1's own geometry from one carrier prefill.

A C1 final export (including CP1 m200) supplies artifact.json, heads.pt, and
full_weights/full_weights.json plus its pinned index and BF16 weight shards
(carrier_c1_run.export). Bundle inputs are its original C1 config JSON, the
config's pinned c1-preparation-v1 receipt, the receipt's pinned model manifest,
and the base directory's small config/tokenizer/processor files. make_bundle
copies only those small files and pins the existing final export in place; it
does not copy base weights or require the training-data closure.

Own heads reproduce CarrierC1.readout with capture_prefix.hidden. The private
vision depth branch still runs its own encoder, as in the official readout;
there is no second LM prefill. Tests compare every value to model.readout.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import resource
import sys
import time

import numpy as np

MDG_ROOT = Path(os.environ.get('RK_MDG_ROOT', '/scratch/jjyeung/orch_cd/mdg_next/work/c1mix_mdg_ro'))
if str(MDG_ROOT) not in sys.path:
    sys.path.insert(0, str(MDG_ROOT))
from student_pilot import mdg_eval as E
from student_pilot.p3_provenance import digest, encoded, file_pin, load, pinned


def bundle(out, **kwargs):
    from student_pilot.mdg_runtime import make_bundle
    return make_bundle(out, **kwargs)


def atomic_json(path, value):
    temporary = path.with_name(path.name+f'.{os.getpid()}.{time.time_ns()}.partial')
    with temporary.open('x') as stream:
        stream.write(encoded(value)+'\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def sync(device):
    import torch
    if torch.device(device).type == 'cuda':
        torch.cuda.synchronize(device)


def grid_points(grid, device):
    import torch
    if type(grid) is not int or grid < 2:
        raise ValueError('Grid must have at least two samples')
    axis = torch.linspace(0, 1000, grid, dtype=torch.float32, device=device)
    v, u = torch.meshgrid(axis, axis, indexing='ij')
    return axis, torch.stack((u, v), -1).reshape(1, -1, 2).expand(32, -1, -1)


def own_heads(model, hidden, batch, grid=51):
    """Equivalent to CarrierC1.readout, retaining the MDG prompt's final states."""
    import torch
    axis, uv = grid_points(grid, hidden.device)
    positions = batch['aux_camera_positions']
    if positions.shape != (1, 32) or not (positions >= 0).all():
        raise ValueError('Own heads require all 32 frame carriers')
    camera = model.auxiliary_heads.pose
    with torch.inference_mode():
        stages, gravity, scale = camera.predict_all(
            camera.carrier_states(hidden.float(), positions), key_mask=positions >= 0)
        if not gravity or not scale or not hasattr(model.auxiliary_heads, 'depth'):
            raise ValueError('Export requires gravity, trajectory scale and private depth')
        prediction = stages[-1]
        fov = prediction[..., 7:9] if model.depth_fov_source == 'pose_head' else None
        depth, _ = model.auxiliary_heads.depth(batch, uv=uv[None], fov=fov)
        return dict(raw_pose=prediction[0].double().cpu().numpy(),
                    gravity_up=gravity[-1][0].double().cpu().numpy(),
                    trajectory_step_m=np.asarray(float(scale[-1][0].exp()), dtype=np.float64),
                    depth_grid=depth.float().cpu().numpy().reshape(32, grid, grid),
                    grid_uv=axis.cpu().numpy())


def predict(model, processor, cfg, entry, names, png_root, device, chunk=8, grid=51):
    import torch
    from student_pilot.carrier_c1_canary import prompt_batch
    from student_pilot.carrier_c1_run import move
    from student_pilot.mdg_features import capture_prefix, suffix_states
    row, audit = E.trainer_row(entry, png_root, E.selection_id(entry))
    with torch.inference_mode():
        batch = move(prompt_batch(processor, row, cfg), device)
        sync(device)
        start = time.perf_counter()
        prefix = capture_prefix(model, batch)
        sync(device)
        prefill_seconds = time.perf_counter()-start
        start = time.perf_counter()
        heads = own_heads(model, prefix.hidden, batch, grid)
        sync(device)
        own_seconds = time.perf_counter()-start
        states = suffix_states(model, prefix, names, chunk=chunk)
        video = model.mdg_head.encode_video(prefix.taps, prefix.vit, prefix.pixels, prefix.grid)
        out = model.mdg_head(video, states.query, states.phrase, states.phrase_mask)[-1]
        values = model.mdg_head.decode(out)
        values.update(clip_prob=out['clip_logit'].sigmoid(), frame_prob=out['frame_logit'].sigmoid())
        values = {k: v.detach().cpu().numpy() if torch.is_tensor(v) else np.asarray(v)
                  for k, v in values.items() if k != 'present'}
    values['area'] = values['area'].astype(np.float64)/np.prod(values['mask'].shape[-2:])
    source_hw = audit['source_height_width']
    if len({tuple(hw) for hw in source_hw}) != 1:
        raise ValueError('Own head export requires constant source resolution')
    heads.update(frame_indices=np.asarray(entry['frame_indices'], np.int64),
                 source_hw=np.asarray(source_hw[0], np.int64))
    audit.update(trainer_prompt_ids_sha256=digest(batch['input_ids'][0].tolist()),
                 processed_height_width=list(prefix.pixels.shape[-2:]),
                 own_heads=dict(path='CarrierC1.readout equivalent on capture_prefix.hidden',
                                lm_prefills=1, extra_lm_prefill_seconds=0.,
                                private_depth_encoder=True, prefill_seconds=prefill_seconds,
                                own_head_seconds=own_seconds))
    return values, heads, audit


def load_runtime(cfg, artifact, mdg, device, bundle_pin, cross_base=False):
    if not cross_base:
        return E.load_runtime(cfg, artifact, mdg, device, bundle_pin)
    from student_pilot.mdg_runtime import load_runtime as base_runtime
    from student_pilot.mdg_features import bind_processor
    from student_pilot.mask_grounding_head import load_artifact
    model, processor, native = base_runtime(
        dict(c1_config=cfg, base_artifact=artifact, bundle=bundle_pin), device)
    if model.mdg_runtime_report['bundle_sha256'] != bundle_pin['sha256']:
        raise ValueError('Loaded bundle identity differs')
    bind_processor(model, processor)
    head, meta = load_artifact(mdg)
    E.frozen_tau(meta)
    model.mdg_head = head.to(device).float().eval().requires_grad_(False)
    model.mdg_meta = meta
    return model, processor, native


def save_heads(path, values, audit):
    validate_heads(values)
    temporary = path.with_name(path.name+f'.{os.getpid()}.{time.time_ns()}.partial')
    with temporary.open('xb') as stream:
        np.savez_compressed(stream, **values, audit=np.asarray(encoded(audit)))
        stream.flush()
        os.fsync(stream.fileno())
    if path.exists():
        raise FileExistsError(path)
    temporary.rename(path)


def validate_heads(values):
    grid = len(values['grid_uv'])
    shapes = dict(raw_pose=(32, 9), gravity_up=(3,), depth_grid=(32, grid, grid),
                  trajectory_step_m=(), frame_indices=(32,), source_hw=(2,), grid_uv=(grid,))
    for key, shape in shapes.items():
        if np.shape(values[key]) != shape or not np.isfinite(values[key]).all():
            raise ValueError('Invalid own heads '+key)
    if values['raw_pose'].dtype != np.float64 or values['depth_grid'].dtype != np.float32:
        raise ValueError('Own head dtype differs')
    if not np.array_equal(values['grid_uv'], np.linspace(0, 1000, grid, dtype=np.float32)):
        # torch.linspace can round an intermediate point by one float32 ulp.
        if not np.allclose(values['grid_uv'], np.linspace(0, 1000, grid), rtol=0, atol=1e-4):
            raise ValueError('Invalid own depth UV grid')


def read_heads(path, binding, key, cross_base):
    with np.load(path, allow_pickle=False) as data:
        values = {k: data[k] for k in data.files if k != 'audit'}
        audit = json.loads(str(data['audit']))
    validate_heads(values)
    if (audit.get('binding') != binding or audit.get('selection') != key
            or audit.get('cross_base') != cross_base):
        raise ValueError('Own heads identity differs')
    return values, audit


def run_export(manifest, png_root, memberships, mdg, t0_config, artifact, out,
               rank=0, world=1, device='cpu', chunk=8, bundle=None, cross_base=False,
               grid=51, first_batch=False):
    import torch
    started = time.perf_counter()
    if (type(world) is not int or world < 1 or type(rank) is not int or not 0 <= rank < world
            or chunk < 1 or type(grid) is not int or grid < 2):
        raise ValueError('Invalid rank/world/chunk/grid')
    if device != 'cpu' and not re.fullmatch(r'cuda:\d+', str(device)):
        raise ValueError('Device must be cpu or cuda:N')
    artifact = E.GH.artifact_pin(artifact) if isinstance(artifact, str) else artifact
    pinned(artifact)
    if bundle is None:
        raise ValueError('Require an explicit bundle')
    bundle_path = Path(bundle)
    bundle_pin = file_pin(bundle_path/'BUNDLE.json' if bundle_path.is_dir() else bundle_path)
    if load(pinned(bundle_pin)).get('schema') != 'mdg-t0-bundle-v1':
        raise ValueError('Require mdg-t0-bundle-v1')
    manifests = [manifest] if isinstance(manifest, (str, Path)) else list(manifest)
    if not manifests:
        raise ValueError('Require at least one manifest')
    entries, first_keys = {}, []
    for path in manifests:
        current = E.manifest_entries(path)
        first_keys.append(sorted(current)[0])
        for key, entry in current.items():
            if key in entries and entries[key] != entry:
                raise ValueError('Conflicting selection identity')
            entries[key] = entry
    groups = E.groups_for(memberships, entries)
    if first_batch:
        if any(k not in groups for k in first_keys):
            raise ValueError('First manifest selection has no membership labels')
        groups = {k: groups[k] for k in sorted(set(first_keys))}
    scenes = [entries[k]['scene'] for k in groups]
    if len(scenes) != len(set(scenes)):
        raise ValueError('Multiple selections would overwrite the same scene heads')
    mdg = Path(mdg)
    meta = load(mdg/'mdg.json')
    tau = E.frozen_tau(meta)
    mismatch = meta.get('base_artifact', {}).get('sha256') != artifact['sha256']
    if mismatch and not cross_base:
        raise ValueError('MDG/base identity differs; require --cross-base')
    output = E.output_root(out)
    output.mkdir(parents=True, exist_ok=True)
    with (output/'binding.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if len(manifests) > 1:
            joined = output/'INPUT_MANIFEST.json'
            E.GH.save_equal(joined, dict(selections=[entries[k] for k in sorted(entries)]))
        else:
            joined = Path(manifests[0])
        request = dict(schema='mdg-export-v1', manifest=file_pin(joined),
            source_manifests=[file_pin(p) for p in manifests], png_root=str(Path(png_root).resolve()),
            memberships=[file_pin(p) for p in memberships], mdg_meta=file_pin(mdg/'mdg.json'),
            mdg_weights=file_pin(mdg/'mdg.pt'), t0_config=file_pin(t0_config), artifact=artifact,
            t0_bundle=bundle_pin, t0_bundle_sha256=bundle_pin['sha256'], world=world, chunk=chunk,
            tau=tau, implementation=file_pin(__file__), groups=groups, grid=grid,
            cross_base=bool(cross_base), base_sha_mismatch=mismatch, first_batch=first_batch)
        E.GH.save_equal(output/'run.json', request)
    binding = digest(request)
    assigned = sorted(groups)[rank::world]
    completed, skipped, batch_reports = {}, 0, []
    if torch.device(device).type == 'cuda' and first_batch:
        torch.cuda.reset_peak_memory_stats(device)
    with (output/f'worker-{rank}.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        journal = output/f'export-{rank}.jsonl'
        if journal.exists():
            for line in journal.read_text().splitlines():
                row = json.loads(line)
                key = row['selection']
                if key not in assigned or row['binding'] != binding or row['rank'] != rank or key in completed:
                    raise ValueError('Export journal identity/shard differs')
                pinned(row['npz'])
                pinned(row['heads_own'])
                completed[key] = row
        runtime = None
        for key in assigned:
            path = output/(key+'.npz')
            head_path = output/'heads_own'/(entries[key]['scene'].replace('/', '__')+'.npz')
            head_path.parent.mkdir(parents=True, exist_ok=True)
            if key in completed:
                if (Path(completed[key]['npz']['path']) != path.resolve()
                        or Path(completed[key]['heads_own']['path']) != head_path.resolve()):
                    raise ValueError('Journal output path identity differs')
                skipped += 1
            elif not path.exists():
                if runtime is None:
                    runtime = load_runtime(request['t0_config'], artifact, mdg, device, bundle_pin, mismatch)
                sync(device)
                begin = time.perf_counter()
                values, heads, audit = predict(*runtime, entries[key], groups[key], png_root, device, chunk, grid)
                sync(device)
                audit.update(binding=binding, selection=key, entry=entries[key], tau=tau,
                    mdg_artifact=dict(meta=request['mdg_meta'], weights=request['mdg_weights']),
                    t0_artifact=artifact, t0_bundle_sha256=bundle_pin['sha256'],
                    cross_base=bool(cross_base), base_sha_mismatch=mismatch,
                    seconds=time.perf_counter()-begin)
                if head_path.exists():
                    old_heads, _ = read_heads(head_path, binding, key, bool(cross_base))
                    if any(not np.array_equal(old_heads[k], heads[k]) for k in heads):
                        raise ValueError('Unjournaled own heads values differ')
                else:
                    save_heads(head_path, heads, audit)
                E.save_npz(path, groups[key], values, audit)
            names, _, audit = E.read_npz(path)
            if (names != groups[key] or audit.get('binding') != binding or audit.get('selection') != key
                    or audit.get('entry') != entries[key] or audit.get('cross_base') != bool(cross_base)):
                raise ValueError('Export identity differs')
            read_heads(head_path, binding, key, bool(cross_base))
            if key not in completed:
                row = dict(selection=key, binding=binding, rank=rank, npz=file_pin(path),
                           heads_own=file_pin(head_path), cross_base=bool(cross_base))
                with journal.open('a') as stream:
                    stream.write(encoded(row)+'\n')
                    stream.flush()
                    os.fsync(stream.fileno())
                completed[key] = row
            batch_reports.append(dict(selection=key, seconds=audit['seconds'], own_heads=audit['own_heads']))
            with (output/'index.lock').open('a') as index_lock:
                fcntl.flock(index_lock, fcntl.LOCK_EX)
                index = load(output/'INDEX.json') if (output/'INDEX.json').exists() else {}
                value = dict(scene=entries[key]['scene'], npz=path.name,
                             heads_own=str(head_path.relative_to(output)), frame_indices=entries[key]['frame_indices'])
                if key in index and index[key] != value:
                    raise ValueError('Index identity differs')
                index[key] = value
                atomic_json(output/'INDEX.json', index)
    result = dict(binding=binding, rank=rank, completed=len(completed), assigned=len(assigned), skipped=skipped)
    if first_batch:
        sync(device)
        report = dict(**result, seconds=time.perf_counter()-started, selections=batch_reports,
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(device) if torch.device(device).type == 'cuda' else 0,
            peak_cuda_reserved_bytes=torch.cuda.max_memory_reserved(device) if torch.device(device).type == 'cuda' else 0,
            cross_base=bool(cross_base), device=str(device))
        with (output/'first-batch.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            reports = load(output/'FIRST_BATCH.json') if (output/'FIRST_BATCH.json').exists() else dict(ranks={})
            reports['ranks'][str(rank)] = report
            atomic_json(output/'FIRST_BATCH.json', reports)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    b = sub.add_parser('bundle')
    for key in ('c1-config', 'receipt', 'model-manifest', 'base-dir', 'artifact-dir', 'out'):
        b.add_argument('--'+key, required=True)
    for command in ('run', 'first-batch'):
        p = sub.add_parser(command)
        p.add_argument('--manifest', action='append', required=True)
        p.add_argument('--membership', action='append', required=True)
        for key in ('png-root', 'mdg', 'bundle', 't0-config', 'artifact', 'out'):
            p.add_argument('--'+key, required=True)
        p.add_argument('--device', default='cpu')
        p.add_argument('--rank', type=int, default=0)
        p.add_argument('--world', type=int, default=1)
        p.add_argument('--grid', type=int, default=51)
        p.add_argument('--chunk', type=int, default=8)
        p.add_argument('--cross-base', action='store_true')
    args = vars(parser.parse_args(argv))
    command = args.pop('command')
    if command == 'bundle':
        args['config'] = args.pop('c1_config')
        result = str(bundle(**args))
    else:
        args['memberships'] = args.pop('membership')
        result = run_export(**args, first_batch=command == 'first-batch')
    print(encoded(result))
    return result


if __name__ == '__main__':
    main()
