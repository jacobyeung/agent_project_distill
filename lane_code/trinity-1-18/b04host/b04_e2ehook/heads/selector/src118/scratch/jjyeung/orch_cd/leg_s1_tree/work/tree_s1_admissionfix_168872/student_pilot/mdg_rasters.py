"""CPU frame-presence and union-mask reads of frozen MDG anchor exports."""
import argparse
from collections import defaultdict
import hashlib
import importlib.util
from pathlib import Path

import numpy as np

from .p3_provenance import file_pin, load, write

EVAL = Path('/scratch/jjyeung/orch_cd/evalx/work')
TP = EVAL/'tp'
GT = Path('/scratch/jjyeung/orch_cd/toolprog/work/gt/scannet')
FROZEN = Path('/scratch/jjyeung/orch_cd/ttower/work/geo_a1/mask_frozen.json')
DEV = EVAL/'devpool/DEV_ITEMS.jsonl'
VSI = Path('/data2/jjyeung/agent_project_data/answerable500_gt_canonical_20260902/answerable500_gt_canonical.json')
VSTI = Path('/home/jjyeung/agent_project/agent/vstibench_repr_450_v3.json')
MIN_VIS = .002
BINS = ('<1%', '1-5%', '>5%')
COUNT_KEYS = ('scene_phrase_pairs', 'frames', 'invalid_frames', 'ignored_frames',
              'gt_present', 'gt_absent', 'tp', 'fn', 'fp', 'tn', 'iou_sum')
METRICS = dict(presence_recall=('tp', 'gt_present'), presence_precision=('tp', 'predicted_present'),
               false_positive_rate=('fp', 'gt_absent'), mask_iou=('iou_sum', 'gt_present'))


def scene_name(value):
    value = str(value)
    if value.startswith('scannet/'):
        value = value[len('scannet/'):]
    if not value or '/' in value or value in ('.', '..') or '\\' in value:
        raise ValueError('Invalid ScanNet scene: '+value)
    return value


def heldout_scenes(frozen, dev, vsi, vsti):
    tuning = {scene_name(s) for s in load(frozen)['tune_scenes']}
    wanted = set()
    with Path(dev).open() as stream:
        import json
        for line in stream:
            q = json.loads(line)
            if q.get('dataset', 'scannet') != 'scannet':
                continue
            scene = scene_name(q['scene_name'])
            if int(hashlib.sha256(scene.encode()).hexdigest(), 16) % 2:
                wanted.add(scene)
    for path, default_dataset in ((vsi, None), (vsti, 'scannet')):
        for q in load(path):
            if q.get('dataset', default_dataset) == 'scannet':
                wanted.add(scene_name(q['scene_name']))
    return wanted-tuning


def label_matcher():
    spec = importlib.util.spec_from_file_location('_mdg_raster_tplib', TP/'tplib.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.match_labels


def nearest_mask(mask, size):
    h, w = size
    mh, mw = mask.shape
    yy = np.minimum(((np.arange(h)+.5)*mh/h).astype(int), mh-1)
    xx = np.minimum(((np.arange(w)+.5)*mw/w).astype(int), mw-1)
    return mask[yy[:, None], xx[None, :]]


def empty_counts():
    return {k: 0. if k == 'iou_sum' else 0 for k in COUNT_KEYS}


def area_bin(area):
    return BINS[0] if area < .01 else BINS[1] if area <= .05 else BINS[2]


def scene_counts(names, values, audit, gt_path, tau, match):
    with np.load(gt_path, allow_pickle=False) as z:
        inst, ids, labels = z['inst'], z['ids'], z['labels'].tolist()
        valid, indices = z['valid'], z['frame_indices']
    if (inst.ndim != 3 or inst.shape[0] != 32 or min(inst.shape[1:]) < 1
            or not np.issubdtype(inst.dtype, np.integer)
            or valid.shape != (32,) or not np.isin(valid, [0, 1]).all()
            or ids.ndim != 1 or len(ids) != len(labels) or len(set(ids.tolist())) != len(ids)
            or not np.issubdtype(ids.dtype, np.integer) or np.any(ids < 0)):
        raise ValueError('Invalid GT raster')
    if indices.shape != (32,) or not np.array_equal(indices, audit['entry']['frame_indices']):
        raise ValueError('GT/MDG anchor mismatch')
    counts = {key: empty_counts() for key in ('overall', *BINS)}
    matched, unmatched = [], []
    for q, name in enumerate(names):
        hits = match(name, list(dict.fromkeys(labels)))
        selected = [int(i) for i, lab in zip(ids, labels) if lab in hits]
        if not selected:
            unmatched.append(name)
            continue
        matched.append(dict(phrase=name, instance_ids=selected))
        counts['overall']['scene_phrase_pairs'] += 1
        touched = set()
        for k in range(32):
            overall = counts['overall']
            overall['frames'] += 1
            if not valid[k]:
                overall['invalid_frames'] += 1
                continue
            gt = np.isin(inst[k], selected)
            pixels = int(gt.sum())
            fraction = pixels/gt.size
            key = area_bin(fraction)
            touched.add(key)
            bucket = counts[key]
            bucket['frames'] += 1
            for row in (overall, bucket):
                if 0 < fraction < MIN_VIS:
                    row['ignored_frames'] += 1
                else:
                    present = fraction >= MIN_VIS
                    predicted = bool(values['prob'][q, k] >= tau)
                    row['gt_present' if present else 'gt_absent'] += 1
                    row[('tp' if predicted else 'fn') if present else ('fp' if predicted else 'tn')] += 1
            if fraction >= MIN_VIS:
                mask = nearest_mask(values['mask'][q, k], gt.shape)
                iou = float(np.count_nonzero(mask & gt)/np.count_nonzero(mask | gt))
                overall['iou_sum'] += iou
                bucket['iou_sum'] += iou
        for key in touched:
            counts[key]['scene_phrase_pairs'] += 1
    return counts, matched, unmatched


def summarize(rows):
    scenes = sorted(rows)
    if not scenes:
        raise ValueError('No held-out scenes with GT-matched exported phrases')
    draws = np.random.default_rng(17).integers(0, len(scenes), size=(2000, len(scenes)))
    result = {}
    for key in ('overall', *BINS):
        counts = {name: sum(rows[s][key][name] for s in scenes) for name in COUNT_KEYS}
        counts['scenes'] = sum(rows[s][key]['frames'] > 0 for s in scenes)
        counts['valid_frames'] = counts['frames']-counts['invalid_frames']
        counts['evaluated_frames'] = counts['gt_present']+counts['gt_absent']
        counts['predicted_present'] = counts['tp']+counts['fp']
        report = dict(counts=counts)
        for metric, (num, den) in METRICS.items():
            numerators = np.array([rows[s][key][num] for s in scenes], dtype=float)
            denominators = np.array([rows[s][key]['tp']+rows[s][key]['fp']
                if den == 'predicted_present' else rows[s][key][den] for s in scenes], dtype=float)
            ns, ds = numerators[draws].sum(1), denominators[draws].sum(1)
            samples = ns[ds > 0]/ds[ds > 0]
            report[metric] = dict(value=float(numerators.sum()/denominators.sum())
                if denominators.sum() else None,
                ci90=np.quantile(samples, [.05, .95]).tolist() if len(samples) else None,
                bootstrap_valid_resamples=len(samples))
        result[key] = report
    return dict(overall=result.pop('overall'), by_gt_area=result)


def export_records(root, meta_pin):
    from . import mdg_eval as E
    root = Path(root)
    if (root/'run.json').exists():
        exports = E.Exports(root)
        if exports.request['mdg_meta']['sha256'] != meta_pin['sha256']:
            raise ValueError('Supplied artifact differs from export')
        for key in sorted(exports.paths):
            entry = exports.entries[key]
            yield entry['scene'], lambda key=key: (*exports.get(key), exports.paths[key])
    else:
        paths = sorted(root.glob('*.npz'))
        if not paths:
            raise ValueError('No export NPZ files')
        for path in paths:
            with np.load(path, allow_pickle=False) as z:
                import json
                audit = json.loads(str(z['audit']))
            yield audit['entry']['scene'], lambda path=path: (*E.read_npz(path), file_pin(path))


def run(export, artifact, out, scenes='heldout', *, gt_root=None, frozen=None,
        dev=None, vsi=None, vsti=None):
    from . import mdg_eval as E
    if scenes != 'heldout':
        raise ValueError('Only the heldout scene split is supported')
    meta_path = Path(artifact)/'mdg.json'
    meta_pin, tau = file_pin(meta_path), E.frozen_tau(load(meta_path))
    paths = dict(frozen=Path(frozen or FROZEN), dev=Path(dev or DEV),
                 vsi=Path(vsi or VSI), vsti=Path(vsti or VSTI))
    split_pins = {key: file_pin(path) for key, path in paths.items()}
    wanted = heldout_scenes(**paths)
    gt_root = Path(gt_root or GT)
    match = label_matcher()
    rows, details, seen = {}, {}, set()
    excluded = defaultdict(int)
    for scene, get in export_records(export, meta_pin):
        if not scene.startswith('scannet/'):
            excluded['non_scannet_exports'] += 1
            continue
        scene = scene_name(scene)
        if scene not in wanted:
            excluded['non_heldout_exports'] += 1
            continue
        if scene in seen:
            raise ValueError('Multiple anchor selections for held-out scene: '+scene)
        seen.add(scene)
        names, values, audit, pin = get()
        if (audit['tau'] != tau
                or audit['mdg_artifact']['meta']['sha256'] != meta_pin['sha256']):
            raise ValueError('NPZ artifact/tau differs')
        if scene_name(audit['entry']['scene']) != scene:
            raise ValueError('NPZ scene differs')
        gt_path = gt_root/(scene+'.npz')
        gt_pin = file_pin(gt_path)
        counts, matched, unmatched = scene_counts(names, values, audit, gt_path, tau, match)
        details[scene] = dict(export=pin, gt=gt_pin, matched=matched, unmatched=unmatched, counts=counts)
        if matched:
            rows[scene] = counts
    if wanted-seen:
        raise ValueError('Missing held-out scene exports: '+', '.join(sorted(wanted-seen)))
    result = summarize(rows)
    recall = result['overall']['presence_recall']['value']
    result.update(schema='mdg-rasters-v1', tau=tau, artifact=meta_pin, split_inputs=split_pins,
        scope='heldout ScanNet; every exported phrase with GT-matched instance IDs; all 32 anchors',
        rules=dict(gt_present='union area >= 0.002', gt_absent='union area == 0',
            ignored='invalid GT frame or 0 < union area < 0.002', mdg_present='prob >= frozen tau',
            precision='TP / (TP + FP) over valid, nonignored frames',
            area_bins='per-frame GT union fraction; zero-area absent frames enter <1%; 1% and 5% enter 1-5%',
            mask_iou='raw union mask, independent of presence; normalized pixel-center nearest resize to GT'),
        bootstrap=dict(unit='scene', resamples=2000, seed=17, confidence=.9,
            estimator='pooled frame ratios; mean per-present-frame IoU',
            undefined='null estimate/CI when denominator is zero; omit zero-denominator resamples'),
        coverage=dict(heldout_scenes=len(wanted), exported_scenes=len(seen),
            scenes_with_matched_phrases=len(rows), excluded_exports=dict(excluded)),
        scenes=details, presence_go=dict(requirement='visible-frame presence recall >= 92%',
            threshold=.92, recall=recall, passed=recall is not None and recall >= .92,
            result='PASS' if recall is not None and recall >= .92 else 'FAIL'))
    if split_pins != {key: file_pin(path) for key, path in paths.items()} or file_pin(meta_path) != meta_pin:
        raise ValueError('Artifact or split inputs changed during evaluation')
    write(out, result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('export', 'artifact', 'out'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--scenes', choices=['heldout'], default='heldout')
    args = parser.parse_args(argv)
    result = run(**vars(args))
    print('Presence GO:', result['presence_go']['result'], result['presence_go']['recall'])


if __name__ == '__main__':
    main()
