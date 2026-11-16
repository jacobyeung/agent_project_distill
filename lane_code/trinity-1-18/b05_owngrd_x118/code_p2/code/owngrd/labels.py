"""Step 2: triage of the SAM 3 teacher output against the GT instance raster (design 3.1 step 2, P7 audit).

Per (frame slot, name), every teacher proposal gets one class:
  POS       joint > POS_JOINT, its majority labelled instance carries the queried name, IoU with it >= POS_IOU,
            and at most half its pixels are unlabelled.
  HARDNEG   joint >= floor and its majority instance carries another name; when that name is a listed confuser
            of the queried one the row trains selection only, at CONFUSER_WEIGHT.
  DISPUTED  joint > POS_JOINT with at least half its pixels unlabelled (no loss; adjudication first).
  DISTILL   anything else (soft score target only).
Per (frame slot, name) the frame gets a presence label only where GT and SAM 3 agree (brief step 2):
  1         at least one POS mask;
  0         ABSENT: no GT pixel of the name in the frame, the name is annotatable for the dataset, the frame is
            valid and SAM 3's presence is under ABSENT_PRESENCE;
  None      otherwise (GT visible but no POS -> MISS rows; GT absent but SAM 3 fires at the native gate ->
            DISPUTED; a sub-threshold sliver of the name; an invalid frame).
MISS rows (GT-visible instance without a POS mask) keep the raster as a low-resolution mask target at
MISS_WEIGHT; P7 measured 36.8% of them wrong, so the default weight is a quarter of the design's start.
Masks are compared at raster resolution: the teacher's frame-size mask is 2x2 box-averaged to the raster.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import sys
from pathlib import Path

import numpy as np

from .common import atomic_write_json, read_json, rle_decode, sha256_file
from .vocab import ARKIT17, MIN_PX, STRUCTURAL, confusers_of, prompt_name

POS_JOINT = 0.5
POS_IOU = 0.5
ABSENT_PRESENCE = 0.2
UNLABELLED_MAX = 0.5
CONFUSER_WEIGHT = 0.25
MISS_WEIGHT = 0.25
SCHEMA = 'owngrd-labels-v1'
RULES = dict(pos_joint=POS_JOINT, pos_iou=POS_IOU, absent_presence=ABSENT_PRESENCE, unlabelled_max=UNLABELLED_MAX,
             confuser_weight=CONFUSER_WEIGHT, miss_weight=MISS_WEIGHT, min_px=MIN_PX)


def to_raster(mask: np.ndarray, hw) -> np.ndarray:
    h, w = hw
    if mask.shape == (h, w):
        return mask
    if mask.shape != (2 * h, 2 * w):
        raise ValueError(f'Teacher mask {mask.shape} is not twice the raster {hw}')
    return mask.reshape(h, 2, w, 2).mean(axis=(1, 3)) >= 0.5


def annotatable(ds: str, name: str, scene_names: set) -> bool:
    """Whether GT can assert the name's absence: ARKitScenes annotates 17 classes; ScanNet(++) annotate densely."""
    if name in STRUCTURAL:
        return False
    if ds == 'arkitscenes':
        return name in ARKIT17
    return True


def triage_frame(inst, valid, id_name, preds, ds, scene_names):
    """Labels for one frame slot: {name: row}. inst: (h, w) int raster, -1 unlabelled."""
    hw = inst.shape
    labelled = inst >= 0
    out = {}
    vis_px = collections.Counter()
    for i, c in zip(*np.unique(inst[labelled], return_counts=True)):
        vis_px[int(i)] = int(c)
    for name, pred in preds.items():
        gt_ids = [i for i, n in id_name.items() if n == name and vis_px.get(i, 0) > 0]
        visible = [i for i in gt_ids if vis_px[i] >= MIN_PX]
        sliver = bool(gt_ids) and not visible
        props, pos_ids = [], set()
        for k, p in enumerate(pred['instances']):
            m = to_raster(rle_decode(p['mask']), hw)
            area = int(m.sum())
            row = {'k': k, 'joint': float(p['joint_score']), 'score': float(p['score']), 'area': area}
            if area == 0:
                row['cls'] = 'DISTILL'
                props.append(row)
                continue
            lab = inst[m & labelled]
            unl = 1.0 - lab.size / area
            row['unlabelled'] = round(unl, 4)
            maj = None
            if lab.size:
                ids, cnt = np.unique(lab, return_counts=True)
                maj = int(ids[np.argmax(cnt)])
                gt = inst == maj
                row['inst'] = maj
                row['iou'] = round(float((m & gt).sum() / (m | gt).sum()), 4)
                row['inst_name'] = id_name.get(maj)
            if not valid:
                row['cls'] = 'DISTILL'
            elif unl > UNLABELLED_MAX:
                row['cls'] = 'DISPUTED' if row['joint'] > POS_JOINT else 'DISTILL'
            elif row.get('inst_name') == name and row['joint'] > POS_JOINT and row['iou'] >= POS_IOU:
                row['cls'] = 'POS'
                pos_ids.add(maj)
            elif maj is not None and row.get('inst_name') != name:
                row['cls'] = 'HARDNEG'
                conf = row.get('inst_name') in confusers_of(name)
                row['selection_only'] = conf
                row['weight'] = CONFUSER_WEIGHT if conf else 1.0
            else:
                row['cls'] = 'DISTILL'
            props.append(row)
        miss = [i for i in visible if i not in pos_ids] if valid else []
        fires = max((p['joint_score'] for p in pred['instances']), default=-1.0) > POS_JOINT
        presence, why = None, None
        if not valid:
            why = 'invalid_frame'
        elif pos_ids:
            presence, why = 1, 'pos'
        elif visible:
            why = 'miss'
        elif sliver:
            why = 'sliver'
        elif not annotatable(ds, name, scene_names):
            why = 'not_annotatable'
        elif pred['presence'] < ABSENT_PRESENCE:
            presence, why = 0, 'absent'
        elif fires:
            why = 'disputed_absent'
        else:
            why = 'uncertain_absent'
        out[name] = {'presence': presence, 'why': why, 'teacher_presence': float(pred['presence']),
                     'gt_visible': visible, 'pos_inst': sorted(pos_ids), 'miss': miss,
                     'miss_weight': MISS_WEIGHT, 'proposals': props}
    return out


def triage_capture(teacher: dict, npz, canonical: str, roles: dict):
    ds = canonical.split('/')[0]
    inst_all, valid_all = npz['inst'], npz['valid']
    id_name = {int(i): prompt_name(str(l)) for i, l in zip(npz['ids'], npz['labels'])}
    scene_names = set(id_name.values())
    if teacher['frame_indices'] != npz['frame_indices'].tolist():
        raise ValueError(f'{canonical}: teacher frame indices differ from the raster')
    frames = {}
    for k, slot in enumerate(teacher['frame_slots']):
        fr = teacher['frames'][str(slot)]
        hw = inst_all[k].shape
        if list(fr['size']) != [2 * hw[0], 2 * hw[1]]:
            raise ValueError(f'{canonical} slot {slot}: frame {fr["size"]} vs raster {hw}')
        frames[str(slot)] = triage_frame(inst_all[k], bool(valid_all[k]), id_name, fr['phrases'], ds, scene_names)
    clip = {}
    for name in teacher['phrases']:
        p = [frames[s][name]['presence'] for s in frames]
        clip[name] = 1 if 1 in p else (0 if p and all(x == 0 for x in p) else None)
    return {'schema': SCHEMA, 'canonical': canonical, 'rules': RULES, 'roles': roles, 'id_name': id_name,
            'raster_hw': list(inst_all.shape[1:]), 'frames': frames, 'clip_presence': clip}


def counts_of(lab):
    c = collections.Counter()
    for fr in lab['frames'].values():
        for name, r in fr.items():
            role = lab['roles'].get(name, '?')
            c[f'presence:{r["why"]}'] += 1
            c[f'presence:{r["why"]}:{role}'] += 1
            c['miss_rows'] += len(r['miss'])
            for p in r['proposals']:
                c[f'prop:{p["cls"]}'] += 1
                if p['cls'] == 'HARDNEG' and p.get('selection_only'):
                    c['prop:HARDNEG:confuser'] += 1
    return c


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--teacher-root', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--gt-root', help='override the manifest GT directory (same file names, hash-checked)')
    a = ap.parse_args(argv)
    from .teacher import capture_key
    man = json.loads(Path(a.manifest).read_text())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    total, done, skipped = collections.Counter(), [], []
    for c in man['captures']:
        d = Path(a.teacher_root) / capture_key(c['canonical'])
        if not (d / 'DONE.json').exists():
            skipped.append(c['canonical'])
            continue
        dj = json.loads((d / 'DONE.json').read_text())
        if sha256_file(d / 'teacher.json.gz') != dj['teacher_sha256']:
            raise ValueError(f'{c["canonical"]}: teacher output hash differs from DONE.json')
        gp = Path(c['gt']['path'])
        if a.gt_root:
            gp = Path(a.gt_root) / gp.relative_to(Path(gp).parents[2])
        if sha256_file(gp) != c['gt']['sha256']:
            raise ValueError(f'{c["canonical"]}: GT raster hash differs from the manifest')
        t = read_json(d / 'teacher.json.gz')
        lab = triage_capture(t, np.load(gp, allow_pickle=False), c['canonical'], {n['name']: n['role'] for n in c['names']})
        lab['teacher_sha256'] = dj['teacher_sha256']
        lab['gt_sha256'] = c['gt']['sha256']
        lab['k1_split'] = c['k1_split']
        atomic_write_json(out / f'{capture_key(c["canonical"])}.labels.json.gz', lab, gz=True)
        total.update(counts_of(lab))
        done.append(c['canonical'])
    summary = {'schema': SCHEMA, 'rules': RULES, 'manifest_sha256': sha256_file(a.manifest), 'captures': len(done),
               'skipped_no_teacher': skipped, 'counts': dict(sorted(total.items()))}
    atomic_write_json(out / 'LABEL_SUMMARY.json', summary)
    print(json.dumps({k: summary[k] for k in ('captures', 'counts')}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
