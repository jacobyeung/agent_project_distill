"""Pinned anchor exports, CPU pointing reads and W10 mask-source conversion."""
import argparse
from collections import defaultdict
import fcntl
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import sys
import time

import numpy as np

from . import grounding_eval as GH
from .p3_provenance import digest, encoded, file_pin, load, pinned, sha256, write

EVAL = Path('/scratch/jjyeung/orch_cd/evalx/work')
SAM = Path('/scratch/jjyeung/orch_cd/ttower/work/sam3_a1')
POINTING = EVAL/'aws_vl/inputs/pointing_membership.json'
GROUND = EVAL/'devpool/GROUND_MEMBERSHIP.json'
ABSENT = SAM.parent/'sam3/scene_absent.json'
BASELINE = EVAL/'out/POINTING_MARKERS_vt_t0m800.json'
SCORER_SHA = '1c9fbacf1de4eb26e084570b2790bf81bacdb7469fb218837def072419e3aebf'


def output_root(path):
    path = Path(path).resolve()
    for root in (EVAL.parents[0], SAM.parents[1], Path('/scratch/jjyeung/orch_cd/ghead')):
        if path.is_relative_to(root):
            raise ValueError('Reference trees are read-only: '+str(path))
    return path


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def label(name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError('Require a nonempty object phrase')
    return name.lower().strip()


def pixel_digest(arrays):
    raw = io.BytesIO()
    np.save(raw, arrays, allow_pickle=False)
    import hashlib
    return hashlib.sha256(raw.getbuffer()).hexdigest()


def selection_id(entry):
    return digest({k: entry[k] for k in ('video_rel', 'frame_indices', 'fps', 'total_num_frames')})


def manifest_entries(path):
    value = load(path)
    rows = value if isinstance(value, list) else value.get('selections', value.get('entries', value.get('items')))
    if not isinstance(rows, list) or not rows:
        raise ValueError('Manifest requires a nonempty selections/entries/items list')
    result = {}
    for original in rows:
        row = dict(original)
        video = Path(row['video_rel'])
        row.setdefault('scene', str(video.with_suffix('')))
        indices, fps, total = row['frame_indices'], row['fps'], row['total_num_frames']
        if (video.is_absolute() or '..' in video.parts or len(indices) != 32 or indices != sorted(indices)
                or type(total) is not int or total < 1 or type(fps) not in (int, float)
                or not math.isfinite(fps) or fps <= 0
                or any(type(i) is not int or not 0 <= i < total for i in indices)
                or len(row['frames']) != 32):
            raise ValueError('Invalid anchor selection')
        for frame, index in zip(row['frames'], indices):
            if 'index' in frame and frame['index'] != index:
                raise ValueError('PNG index differs from selection')
        for key in ('anchor_pixel_sha256', 'duplicate_pixel_sha256'):
            if not re.fullmatch('[0-9a-f]{64}', row[key]):
                raise ValueError('Invalid anchor pixel pin')
        key = selection_id(row)
        if key in result:
            raise ValueError('Duplicate anchor selection')
        result[key] = row
    return result


def trainer_row(entry, png_root, qid):
    from PIL import Image
    from .grounding_train import QUESTION
    root = Path(png_root).resolve(strict=True)
    frames, arrays = [], []
    for pin in entry['frames']:
        value = pin.get('path', pin.get('png'))
        path = Path(value)
        path = (path if path.is_absolute() else root/path).resolve(strict=True)
        if not path.is_relative_to(root):
            raise ValueError('PNG escaped the supplied root')
        frame = dict(path=str(path), sha256=pin['sha256'])
        with Image.open(pinned(frame)) as image:
            if image.mode != 'RGB' or image.format != 'PNG':
                raise ValueError('Require lossless RGB PNG')
            arrays.append(np.array(image))
        frames.append(frame)
    arrays = np.stack(arrays)
    if (pixel_digest(arrays) != entry['anchor_pixel_sha256']
            or pixel_digest(np.repeat(arrays, 2, axis=0)) != entry['duplicate_pixel_sha256']):
        raise ValueError('Decoded anchor/duplicate pixels differ')
    row = dict(qid=qid, target='<think>\n\n</think>\n\n{"point_2d": null}', student_input=dict(
        frames=frames, frame_indices=entry['frame_indices'],
        timestamps=[i/entry['fps'] for i in entry['frame_indices']], fps=entry['fps'],
        total_num_frames=entry['total_num_frames'], question=QUESTION, options=[]))
    audit = {k: entry[k] for k in ('anchor_pixel_sha256', 'duplicate_pixel_sha256')}
    audit.update(png_sha256=[p['sha256'] for p in frames],
                 source_height_width=[list(a.shape[:2]) for a in arrays])
    return row, audit


def members(path):
    value = load(path)
    rows = value['items'] if isinstance(value, dict) else value
    result, seen = [], set()
    for original in rows:
        if original.get('kind', 'point') != 'point':
            continue
        row = dict(original, id=str(original['id']))
        scene = row.get('scene', row.get('scene_key'))
        if not scene or not re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9_-]+', scene):
            raise ValueError('Require a safe dataset/scene identity')
        row['scene'] = scene
        if row['id'] in seen or type(row['frame']) is not int or not 1 <= row['frame'] <= 32:
            raise ValueError('Duplicate item or invalid frame')
        seen.add(row['id'])
        label(row['obj'])
        result.append(row)
    return result


def selection_for(item, entries):
    found = []
    for key, entry in entries.items():
        if item['scene'] != entry['scene']:
            continue
        if any(k in item and item[k] != entry[k]
               for k in ('video_rel', 'frame_indices', 'fps', 'total_num_frames')):
            continue
        if 'source_index' in item and item['source_index'] != entry['frame_indices'][item['frame']-1]:
            continue
        found.append(key)
    if len(found) != 1:
        raise ValueError('Missing or ambiguous anchor selection for '+item['id'])
    return found[0]


def groups_for(paths, entries):
    groups = defaultdict(set)
    for path in paths:
        for item in members(path):
            groups[selection_for(item, entries)].add(label(item['obj']))
    return {key: sorted(names) for key, names in sorted(groups.items())}


def frozen_tau(meta):
    tau = meta.get('tau')
    if type(tau) not in (int, float) or not math.isfinite(tau) or not 0 <= tau <= 1:
        raise ValueError('MDG artifact requires frozen tau in [0,1]')
    return tau


def load_runtime(cfg, artifact, directory, device, bundle):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('student_pilot/mdg_eval.py:load_runtime')
    from .mdg_runtime import load_runtime as base_runtime
    from .mdg_features import bind_processor
    from .mask_grounding_head import load_artifact
    model, processor, native = base_runtime(dict(c1_config=cfg, base_artifact=artifact, bundle=bundle), device)
    if model.mdg_runtime_report['bundle_sha256'] != bundle['sha256']:
        raise ValueError('Loaded T0 bundle differs')
    bind_processor(model, processor)
    head, meta = load_artifact(directory)
    if meta.get('base_artifact', {}).get('sha256') != artifact['sha256']:
        raise ValueError('MDG was trained against another T0 artifact')
    frozen_tau(meta)
    from .mdg_lora import load as load_lora
    load_lora(model, directory, meta)
    if meta.get('lora_config'):
        model.auxiliary_heads.mdg_lora.to(device).float().eval().requires_grad_(False)
    head = head.to(device).float().eval().requires_grad_(False)
    model.mdg_head, model.mdg_meta = head, meta
    return model, processor, native


def predict(model, processor, cfg, entry, names, png_root, device, chunk):
    import torch
    from .carrier_c1_canary import prompt_batch
    from .carrier_c1_run import move
    from .mdg_features import capture_prefix
    from .mdg_stream import stream_suffix_states, decoder_output
    row, audit = trainer_row(entry, png_root, selection_id(entry))
    with torch.inference_mode():
        batch = move(prompt_batch(processor, row, cfg), device)
        prefix = capture_prefix(model, batch)
        states = stream_suffix_states(model, prefix, batch, names, chunk=chunk)
        video = model.mdg_head.encode_video(prefix.taps, prefix.vit, prefix.pixels, prefix.grid)
        out = decoder_output(model.mdg_head, video, states)
        values = model.mdg_head.decode(out)
        values.update(clip_prob=out['clip_logit'].sigmoid(), frame_prob=out['frame_logit'].sigmoid())
        values = {k: v.detach().cpu().numpy() if torch.is_tensor(v) else np.asarray(v)
                  for k, v in values.items() if k != 'present'}
    # The decoder returns positive-cell counts; the export stores the fraction of the mask grid.
    values['area'] = values['area'].astype(np.float64) / np.prod(values['mask'].shape[-2:])
    audit.update(continuation='native_single_token_v1', trainer_prompt_ids_sha256=digest(batch['input_ids'][0].tolist()),
                 processed_height_width=list(prefix.pixels.shape[-2:]))
    return values, audit


def validate_arrays(values, names):
    q = len(names)
    if names != sorted(set(map(label, names))):
        raise ValueError('Export names must be normalized, unique and sorted')
    shapes = dict(prob=(q, 32), clip_prob=(q,), frame_prob=(q, 32), iou=(q, 32),
                  uv=(q, 32, 2), area=(q, 32))
    for key, shape in shapes.items():
        a = np.asarray(values[key])
        if a.shape != shape or not np.isfinite(a).all():
            raise ValueError('Invalid export '+key)
        if key != 'uv' and (np.any(a < 0) or np.any(a > 1)):
            raise ValueError('Export probability/area outside [0,1]')
    uv = values['uv']
    if np.any(uv != np.rint(uv)) or np.any(uv < 0) or np.any(uv > 1000):
        raise ValueError('Invalid canvas coordinates')
    mask = np.asarray(values['mask'])
    if mask.dtype != bool or mask.ndim != 4 or mask.shape[:2] != (q, 32) or min(mask.shape[-2:]) < 1:
        raise ValueError('Invalid export masks')
    if not np.allclose(values['prob'], values['clip_prob'][:, None]*values['frame_prob'], atol=1e-6):
        raise ValueError('Joint probabilities differ')


def save_npz(path, names, values, audit):
    validate_arrays(values, names)
    payload = {k: values[k] for k in ('prob', 'clip_prob', 'frame_prob', 'iou', 'uv', 'area')}
    payload.update(names=np.array(names), masks=np.packbits(values['mask'], axis=-1, bitorder='little'),
                   mask_shape=np.array(values['mask'].shape), audit=np.array(encoded(audit)))
    temporary = path.with_name(path.name+f'.{time.time_ns()}.partial')
    with temporary.open('xb') as stream:
        np.savez_compressed(stream, **payload)
        stream.flush()
        os.fsync(stream.fileno())
    if path.exists():
        raise FileExistsError(path)
    temporary.rename(path)


def read_npz(path):
    with np.load(path, allow_pickle=False) as z:
        values = {k: z[k].copy() for k in ('prob', 'clip_prob', 'frame_prob', 'iou', 'uv', 'area')}
        shape = tuple(z['mask_shape'].tolist())
        values['mask'] = np.unpackbits(z['masks'], axis=-1, count=shape[-1], bitorder='little').astype(bool)
        names, audit = z['names'].tolist(), json.loads(str(z['audit']))
    if values['mask'].shape != shape:
        raise ValueError('Packed mask shape differs')
    validate_arrays(values, names)
    return names, values, audit


def run_export(manifest, png_root, memberships, mdg, t0_config, artifact, out, rank=0, world=1,
               device='cpu', chunk=8, t0_bundle=None):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('student_pilot/mdg_eval.py:run_export')
    if type(world) is not int or world < 1 or type(rank) is not int or not 0 <= rank < world or chunk < 1:
        raise ValueError('Invalid rank/world/chunk')
    artifact = GH.artifact_pin(artifact) if isinstance(artifact, str) else artifact
    pinned(artifact)
    if t0_bundle is None:
        raise ValueError('Require an explicit T0 bundle')
    bundle_path = Path(t0_bundle)
    bundle = file_pin(bundle_path/'BUNDLE.json' if bundle_path.is_dir() else bundle_path)
    if load(pinned(bundle)).get('schema') != 'mdg-t0-bundle-v1':
        raise ValueError('Require mdg-t0-bundle-v1')
    entries = manifest_entries(manifest)
    groups = groups_for(memberships, entries)
    mdg = Path(mdg)
    meta = load(mdg/'mdg.json')
    tau = frozen_tau(meta)
    if meta.get('base_artifact', {}).get('sha256') != artifact['sha256']:
        raise ValueError('MDG/T0 identity differs')
    request = dict(schema='mdg-export-v1', manifest=file_pin(manifest), png_root=str(Path(png_root).resolve()),
        memberships=[file_pin(p) for p in memberships], mdg_meta=file_pin(mdg/'mdg.json'),
        mdg_weights=file_pin(mdg/'mdg.pt'), t0_config=file_pin(t0_config), artifact=artifact,
        t0_bundle=bundle, t0_bundle_sha256=bundle['sha256'], world=world, chunk=chunk, tau=tau,
        implementation=file_pin(__file__), groups=groups,
        continuation='native_single_token_v1', stream_implementation=file_pin(Path(__file__).with_name('mdg_stream.py')))
    if meta.get('lora_config'):
        request['mdg_lora'] = file_pin(pinned(dict(path=str(mdg/'lora.pt'),
                                                 sha256=meta['lora_weights']['sha256'])))
    binding = digest(request)
    output = output_root(out)
    output.mkdir(parents=True, exist_ok=True)
    with (output/'binding.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        GH.save_equal(output/'run.json', request)
    assigned = sorted(groups)[rank::world]
    with (output/f'worker-{rank}.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        journal = output/f'export-{rank}.jsonl'
        completed = {}
        if journal.exists():
            for line in journal.read_text().splitlines():
                row = json.loads(line)
                key = row['selection']
                if key not in assigned or row['binding'] != binding or row['rank'] != rank or key in completed:
                    raise ValueError('Export journal identity/shard differs')
                pinned(row['npz'])
                completed[key] = row
        pending = [key for key in assigned if key not in completed]
        runtime = load_runtime(request['t0_config'], artifact, mdg, device, bundle) if pending else None
        for key in assigned:
            path = output/(key+'.npz')
            if key not in completed:
                if not path.exists():
                    started = time.perf_counter()
                    model, processor, cfg = runtime
                    values, audit = predict(model, processor, cfg, entries[key], groups[key], png_root, device, chunk)
                    audit.update(binding=binding, selection=key, entry=entries[key], tau=tau,
                        mdg_artifact=dict(meta=request['mdg_meta'], weights=request['mdg_weights']),
                        t0_artifact=artifact, t0_bundle_sha256=request['t0_bundle_sha256'],
                        seconds=time.perf_counter()-started)
                    save_npz(path, groups[key], values, audit)
                names, _, audit = read_npz(path)
                if names != groups[key] or audit.get('binding') != binding or audit.get('selection') != key:
                    raise ValueError('Unjournaled export identity differs')
                row = dict(selection=key, binding=binding, rank=rank, npz=file_pin(path))
                with journal.open('a') as stream:
                    stream.write(encoded(row)+'\n')
                    stream.flush()
                    os.fsync(stream.fileno())
                completed[key] = row
            names, _, audit = read_npz(pinned(completed[key]['npz']))
            if names != groups[key] or audit['binding'] != binding:
                raise ValueError('Completed export identity differs')
    return dict(binding=binding, rank=rank, completed=len(completed), assigned=len(assigned))


class Exports:
    def __init__(self, root):
        self.root = Path(root)
        self.request = load(self.root/'run.json')
        if self.request.get('schema') != 'mdg-export-v1':
            raise ValueError('Require mdg-export-v1')
        self.binding = digest(self.request)
        self.entries = manifest_entries(pinned(self.request['manifest']))
        meta = load(pinned(self.request['mdg_meta']))
        self.tau = frozen_tau(meta)
        if self.tau != self.request['tau']:
            raise ValueError('Frozen tau differs')
        self.paths = {}
        for rank in range(self.request['world']):
            expected = set(sorted(self.request['groups'])[rank::self.request['world']])
            seen = set()
            path = self.root/f'export-{rank}.jsonl'
            if not path.exists():
                if not expected:
                    continue
                raise ValueError('Missing export shard')
            for line in path.read_text().splitlines():
                row = json.loads(line)
                key = row['selection']
                if row['binding'] != self.binding or row['rank'] != rank or key not in expected or key in seen:
                    raise ValueError('Export journal differs')
                seen.add(key)
                self.paths[key] = row['npz']
            if seen != expected:
                raise ValueError('Incomplete export shard')
        self.cached = None

    def get(self, key):
        if self.cached is None or self.cached[0] != key:
            names, values, audit = read_npz(pinned(self.paths[key]))
            if (audit['binding'] != self.binding or audit['selection'] != key
                    or audit['entry'] != self.entries[key] or names != self.request['groups'][key]
                    or audit['tau'] != self.tau):
                raise ValueError('NPZ audit differs')
            self.cached = key, names, values, audit
        return self.cached[1:]

    def item(self, item):
        key = selection_for(item, self.entries)
        names, values, audit = self.get(key)
        q = names.index(label(item['obj']))
        return {k: v[q].tolist() for k, v in values.items() if k != 'mask'}, audit


def task_for(item, entry):
    k = item['frame']
    return dict(benchmark='pointing_video', example_id=item['id']+':A', membership_id=item['id'],
        variant='A', scene=item['scene'], obj=item['obj'], frame=k, source_index=entry['frame_indices'][k-1])


def record_for(item, exports):
    prediction, audit = exports.item(item)
    task = task_for(item, audit['entry'])
    record = GH.record_for(task, prediction, exports.tau, exports.binding, 0,
        {k: audit[k] for k in ('processed_height_width', 'trainer_prompt_ids_sha256',
                               'anchor_pixel_sha256', 'duplicate_pixel_sha256')})
    record.pop('gh')
    record.update(model='mdg', attempt='mdg', accepted_presence=prediction['prob'][item['frame']-1] >= exports.tau,
                  mdg=dict(prediction, tau=exports.tau, artifact=audit['mdg_artifact'],
                           t0_bundle_sha256=audit['t0_bundle_sha256'], selection=audit['selection']))
    return record


def journal_equal(path, rows):
    text = ''.join(encoded(row)+'\n' for row in rows)
    path = Path(path)
    if path.exists():
        if path.read_text() != text:
            raise ValueError('Existing records differ')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x') as stream:
            stream.write(text)


def score_tools():
    common = module_at('_mdg_sam_common', SAM/'common.py')
    score = common.video_scorer()
    if sha256(score.__file__) != SCORER_SHA:
        raise ValueError('GH0 pointing scorer changed')
    return score


def score_records(items, rows, score, gt_roots, programs_path):
    if len(rows) != len(items) or {r['membership_id'] for r in rows} != {r['id'] for r in items}:
        raise ValueError('Pointing coverage differs')
    by = defaultdict(list)
    record_index = {r['membership_id']: r for r in rows}
    for item in items:
        by[item['scene']].append(item)
    programs = score.programs(programs_path)
    result = []
    for scene, group in sorted(by.items()):
        dataset = scene.split('/')[0]
        if dataset not in gt_roots:
            raise ValueError('Require explicit GT root for '+dataset)
        gg = score.ground(scene, Path(gt_roots[dataset]), programs)
        for item in group:
            k = item['frame']
            if not gg.gt.valid[k-1]:
                raise ValueError('Invalid selected GT frame')
            masks = [m for _, m in gg.masks(item['obj'], k)]
            row = record_index[item['id']]
            value = score.score_mask(row['raw_generation'], masks, row['processed_height_width'])
            union = np.logical_or.reduce(masks) if masks else None
            area = float(union.mean()) if union is not None else 0.
            result.append(dict(example_id=item['id'], scene=scene, obj=item['obj'], dataset=dataset,
                frame=k, area=area, area_bin='<1%' if area < .01 else '1-5%' if area <= .05 else '>5%',
                **value, **value['parsings']['xy_1000']))
    return result


def bootstrap(rows, field, samples=4000):
    by = defaultdict(lambda: [0., 0.])
    for row in rows:
        by[row['scene']][0] += row[field]
        by[row['scene']][1] += 1
    if not by:
        return dict(n=0, value=None, ci90=None, scenes=0)
    a = np.array([by[k] for k in sorted(by)])
    rng = np.random.default_rng(17)
    draws = rng.integers(0, len(a), (samples, len(a)))
    total = a[draws].sum(1)
    return dict(n=len(rows), value=float(a[:, 0].sum()/a[:, 1].sum()),
                ci90=np.quantile(total[:, 0]/total[:, 1], [.05, .95]).tolist(), scenes=len(a))


def baseline_rows(path):
    value = load(path)
    rows = value['models']['t0m800']['conditions']['markers_on']['items']
    rows = [r for r in rows if r.get('variant') == 'A']
    result = {}
    for row in rows:
        key = str(row.get('membership_id', row['example_id'].removesuffix(':A')))
        if key in result:
            raise ValueError('Duplicate T0 item')
        result[key] = dict(row, **row['parsings']['xy_1000'])
    return result


def report_pointing(scored, baseline, absent, samples):
    if {r['example_id'] for r in scored} != set(baseline):
        raise ValueError('T0/MDG paired item coverage differs')
    paired = []
    for row in scored:
        base = baseline[row['example_id']]
        if (base['scene'], base['visible']) != (row['scene'], row['visible']):
            raise ValueError('T0/MDG scene or visibility differs')
        paired.append(dict(row, gain=row['inside']-base['inside']))
    def summary(rows):
        visible = [r for r in rows if r['visible']]
        return dict(in_mask=bootstrap(visible, 'inside', samples),
            null_on_absent=bootstrap([r for r in rows if not r['visible']], 'none_score', samples),
            paired_in_mask_vs_t0=bootstrap(visible, 'gain', samples),
            area_bins={b: bootstrap([r for r in visible if r['area_bin'] == b], 'inside', samples)
                       for b in ('<1%', '1-5%', '>5%')})
    return dict(all=summary(paired),
        datasets={ds: summary([r for r in paired if r['dataset'] == ds]) for ds in ('scannet', 'arkit')},
        scene_absent_fp=bootstrap([dict(r, fp=float(r['accepted_presence'])) for r in absent], 'fp', samples),
        confidence=.9, seed=17, bootstrap_samples=samples)


def run_pointing(export, pointing, ground, absent, out, baseline=BASELINE, gt_roots=None,
                 programs_path=None, samples=4000):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('student_pilot/mdg_eval.py:run_pointing')
    exports = Exports(export)
    output = output_root(out)
    output.mkdir(parents=True, exist_ok=True)
    memberships = dict(pointing=pointing, ground=ground, scene_absent=absent)
    rows_by = {}
    for name, path in memberships.items():
        if file_pin(path) not in exports.request['memberships']:
            raise ValueError('Membership was not frozen into this export')
        items = members(path)
        rows = [record_for(item, exports) for item in items]
        journal_equal(output/(name+'.jsonl'), rows)
        rows_by[name] = rows
    directory = output/'ground/ground_mdg_t0m800'
    if not directory.exists():
        GH.to_ground(output/'ground.jsonl', ground, 'mdg_t0m800', output/'ground')
    else:
        expected = defaultdict(dict)
        for row in rows_by['ground']:
            expected[row['scene']][row['membership_id']] = row['response_text']
        for scene, values in expected.items():
            if load(directory/(scene.replace('/', '__')+'.json')) != dict(scene=scene, out=values):
                raise ValueError('Ground outputs differ')
    score = score_tools()
    membership = load(pointing)
    score.validate_pointing(membership)
    programs_path = programs_path or score.TOOL/'tp/programs.py'
    if membership.get('sources', {}).get('programs') != sha256(programs_path):
        raise ValueError('Pointing GT source pin differs')
    scored = score_records(members(pointing), rows_by['pointing'], score,
        gt_roots or dict(scannet=score.TOOL/'gt/scannet'), programs_path)
    if len(scored) == 1000 and sum(r['visible'] for r in scored) != 650:
        raise ValueError('GT visibility differs from 650/350')
    result = report_pointing(scored, baseline_rows(baseline), rows_by['scene_absent'], samples)
    result.update(binding=exports.binding, tau=exports.tau, baseline=file_pin(baseline),
        baseline_cell='models/t0m800/conditions/markers_on/variant-A', scorer=file_pin(score.__file__),
        memberships={k: file_pin(v) for k, v in memberships.items()},
        gt_roots={k: str(v) for k, v in (gt_roots or dict(scannet=score.TOOL/'gt/scannet')).items()},
        definitions=dict(area='un-eroded GT instance union / frame area',
                         inside='GH0 xy_1000: 2px erosion per instance, <8-cell fallback',
                         paired='MDG minus T0, identical visible items, seed-17 scene bootstrap'))
    GH.save_equal(output/'pointing_scored.json', dict(items=scored))
    GH.save_equal(output/'report.json', result)
    return result


def rle(mask):
    a = np.asarray(mask, bool).ravel(order='F').astype(np.uint8)
    changes = np.flatnonzero(np.diff(a))+1
    counts = np.diff(np.r_[0, changes, a.size]).tolist()
    if a.size and a[0]:
        counts.insert(0, 0)
    return dict(size=list(mask.shape), counts=counts)


def resize_mask(mask, height_width):
    from PIL import Image
    h, w = height_width
    return np.asarray(Image.fromarray(mask).resize((w, h), Image.Resampling.NEAREST), bool)


def mask_record(values, q, k, size, tau):
    mask = resize_mask(values['mask'][q, k], size)
    yy, xx = np.nonzero(mask)
    prob = float(values['prob'][q, k])
    instances = []
    if len(xx):
        instances = [dict(query=0, score=float(values['frame_prob'][q, k]),
                          box=[int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1)], mask=rle(mask))]
    return dict(instances=instances, click=values['uv'][q, k].tolist(),
                presence=float(values['clip_prob'][q]), joint_score=prob), bool(instances and prob >= tau)


def run_w10(export, membership, out, tag='mdg_t0m800'):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('student_pilot/mdg_eval.py:run_w10')
    if not re.fullmatch('[A-Za-z0-9_-]{1,64}', tag):
        raise ValueError('Unsafe W10 tag')
    exports = Exports(export)
    if file_pin(membership) not in exports.request['memberships']:
        raise ValueError('W10 membership was not frozen into export')
    by = defaultdict(list)
    for item in members(membership):
        if item['scene'].startswith('scannet/'):
            by[item['scene']].append(item)
    root = output_root(out)
    files, selections = {}, {}
    for scene, items in sorted(by.items()):
        keys = {selection_for(item, exports.entries) for item in items}
        if len(keys) != 1:
            raise ValueError('W10 requires one anchor selection per scene')
        names, values, audit = exports.get(next(iter(keys)))
        selections[scene] = dict(selection=audit['selection'], frame_indices=audit['entry']['frame_indices'],
            fps=audit['entry']['fps'], total_num_frames=audit['entry']['total_num_frames'],
            anchor_pixel_sha256=audit['anchor_pixel_sha256'])
        objects, recs = {}, {}
        for q, name in enumerate(names):
            slots = {}
            for k in range(32):
                record, accepted = mask_record(values, q, k, audit['source_height_width'][k], exports.tau)
                recs[name, k] = record, accepted
                if accepted:
                    slots[str(k)] = record
            first = min(map(int, slots)) if slots else None
            objects[name] = dict(first_seen_slot=first, first_seen_anchor=first+1 if first is not None else None,
                                 accepted_slots=slots)
        output, grouped = {}, defaultdict(list)
        for item in items:
            grouped[label(item['obj'])].append(item)
        for name, group in grouped.items():
            acc = sorted([(recs[name, it['frame']-1][0]['joint_score'], it['id']) for it in group
                          if recs[name, it['frame']-1][1]], reverse=True)
            keep = {identity for _, identity in acc[:1]}
            for item in group:
                point = recs[name, item['frame']-1][0]['click'] if item['id'] in keep else None
                output[item['id']] = json.dumps([dict(point_2d=point)], allow_nan=False)
        filename = scene.replace('/', '__')+'.json'
        GH.save_equal(root/'ground'/('ground_'+tag+'top1x')/filename, dict(scene=scene, out=output))
        GH.save_equal(root/'lifting'/tag/filename,
            dict(scene=scene, tau=exports.tau, slot_base=0, inference_only=True, objects=objects))
        for relative in (Path('ground')/('ground_'+tag+'top1x')/filename, Path('lifting')/tag/filename):
            files[str(relative)] = sha256(root/relative)
    receipt = dict(schema='mdg-w10-source-v1', binding=exports.binding, tag=tag, tau=exports.tau,
        membership=file_pin(membership), scenes=len(by), files=files, selections=selections,
        mask_semantics='one union mask per label; ambiguity scores contain one instance',
        frame_selection='emit_topk: highest joint score then highest item ID; top 1 membership item',
        lifting='emit.lifting: every nonempty mask with joint probability >= frozen tau')
    GH.save_equal(root/'source.json', receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='phase', required=True)
    export = commands.add_parser('export')
    for key in ('manifest', 'png-root', 'mdg', 't0-config', 't0-bundle', 'artifact', 'out'):
        export.add_argument('--'+key, required=True)
    export.add_argument('--membership', action='append', required=True)
    export.add_argument('--rank', type=int, default=0)
    export.add_argument('--world', type=int, default=1)
    export.add_argument('--device', default='cpu')
    export.add_argument('--chunk', type=int, default=8)
    pointing = commands.add_parser('pointing')
    pointing.add_argument('--export', required=True)
    pointing.add_argument('--out', required=True)
    for key, default in (('pointing', POINTING), ('ground', GROUND), ('absent', ABSENT), ('baseline', BASELINE)):
        pointing.add_argument('--'+key, default=str(default))
    pointing.add_argument('--gt-scannet')
    pointing.add_argument('--gt-arkit')
    pointing.add_argument('--programs')
    pointing.add_argument('--samples', type=int, default=4000)
    w10 = commands.add_parser('w10')
    w10.add_argument('--export', required=True)
    w10.add_argument('--membership', default=str(GROUND))
    w10.add_argument('--out', required=True)
    w10.add_argument('--tag', default='mdg_t0m800')
    args = vars(parser.parse_args(argv))
    phase = args.pop('phase')
    if phase == 'export':
        args['memberships'] = args.pop('membership')
        result = run_export(**args)
    elif phase == 'pointing':
        roots = {k: args.pop('gt_'+k) for k in ('scannet', 'arkit')}
        roots = {k: v for k, v in roots.items() if v}
        args['gt_roots'] = roots or None
        args['programs_path'] = args.pop('programs')
        result = run_pointing(**args)
    else:
        result = run_w10(**args)
    print(encoded(result))


if __name__ == '__main__':
    main()
