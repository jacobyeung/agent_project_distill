"""STAB design facts: counts of captures and items only (no score, no accuracy, no paired difference)."""
import collections, hashlib, json, sys, tarfile
from pathlib import Path
import numpy as np
K5 = Path('/scratch/jjyeung/orch_n30/lever6/k5b')
sys.path.insert(0, str(K5/'kit'))
import score_k5 as sk
HERE = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ref_all = json.loads((K5/'kit/REFERENCE_K5.json').read_text())
ref = {c['k']: c for c in ref_all['captures']}
keys = [c['k'] for c in sorted(ref_all['captures'], key=lambda c: c['position'])]
n = len(keys)
arms = sk.arms_from([sk.authenticated(K5/'ret/g0', 0), sk.authenticated(K5/'ret/g1', 1)])
p1 = sk.pair(arms, 0, 2, keys, n, ref)
split = json.loads(Path('/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t1/CAMERA_SPLIT.json').read_text())
audited = {c['capture'] for c in split['captures']}
nogt = set()
for t in ('/scratch/jjyeung/orch_n30/lever1_c/arch5/nogt_gt15_20261120.tar', '/scratch/jjyeung/orch_n30/lever1_c/arch6/nogt_arkit7_20261120.tar'):
    for m in tarfile.open(t).getnames():
        if m.endswith('.npz'):
            nm = Path(m).name[:-4]
            nogt.add(nm.replace('__', '/') if '__' in nm else 'arkitscenes/'+nm)
camgt = {p.name[:-4].replace('__', '/') for p in Path('/scratch/jjyeung/orch_n30/cont_ops25_c/cam/gt/t1_gt/gt').glob('*.npz')}
items = json.loads(Path('/scratch/jjyeung/orch_n30/lever7/nfa/ref/payload/items/devs1_routed.json').read_text())['items']
rows = []
for k in keys:
    r = ref[k]; c = r['capture']; pc = p1['per_capture'][k]
    rows.append(dict(capture=c, k=k, dataset=r['dataset'], position=r['position'], frames=r['frames'], rank1=r['rank1'],
                     audited=c in audited, nogt_npz=c in nogt, cam_gt_npz=c in camgt,
                     dis_rot_deg=pc['rotation_deg'], dis_trans=pc['translation_m'], metric_scale=bool(r['rank1'])))
caps = {r['capture'] for r in rows}
def ds(scene): return {'scannet': 'ScanNet', 'scannetppv2': 'ScanNet++', 'arkitscenes': 'ARKit'}[scene.split('/')[0]]
TYPES = ('camera_displacement', 'camera_rotation', 'camera_movement_direction', 'object_abs_distance', 'room_size_estimation')
cov = {t: collections.Counter() for t in TYPES}; capc = {t: collections.defaultdict(set) for t in TYPES}
unc = collections.Counter()
for it in items:
    t, s = it['question_type'], it['scene']
    if s in caps:
        cov[t][ds(s)] += 1; capc[t][ds(s)].add(s)
    else:
        unc[t] += 1
# thresholds (rotation, deg; scale-free, valid on all 84)
t1 = json.loads((HERE/'t1rep.json').read_text())['scannet/scene0515_00']
T1_ROT = max(t1['rot_deg']); T1_TRANS = max(t1['trans_m'])
def flagged(th, sel):
    return [r['capture'] for r in sel if r['dis_rot_deg'] > th]
out46 = [r for r in rows if not r['audited']]
res = dict(schema='stab-facts-v1', note='counts and camera differences only; no score, accuracy or paired difference was computed',
    k5_captures=n, by_dataset=dict(collections.Counter(r['dataset'] for r in rows)),
    audited38=sum(r['audited'] for r in rows), outside38=len(out46),
    outside38_gt=dict(nogt_npz=sum(r['nogt_npz'] for r in out46), cam_gt_npz_only=sum((not r['nogt_npz']) and r['cam_gt_npz'] for r in out46),
                      no_gt_file_here=sum((not r['nogt_npz']) and (not r['cam_gt_npz']) for r in out46),
                      outside38_by_dataset=dict(collections.Counter(r['dataset'] for r in out46)),
                      nogt_by_dataset=dict(collections.Counter(r['dataset'] for r in out46 if r['nogt_npz'])),
                      camgt_only_by_dataset=dict(collections.Counter(r['dataset'] for r in out46 if (not r['nogt_npz']) and r['cam_gt_npz'])),
                      none_by_dataset=dict(collections.Counter(r['dataset'] for r in out46 if (not r['nogt_npz']) and (not r['cam_gt_npz']))),
                      none_list=sorted(r['capture'] for r in out46 if (not r['nogt_npz']) and (not r['cam_gt_npz']))),
    t1_repeat=dict(capture='scannet/scene0515_00', repeats=len(t1['rot_deg']), rot_deg=T1_ROT, centre_m=T1_TRANS,
                   history_diag_elementwise_m=0.00186),
    flags_by_rotation_threshold={}, items_on_k5=dict((t, dict(cov[t])) for t in TYPES),
    captures_on_k5=dict((t, {d: len(v) for d, v in capc[t].items()}) for t in TYPES), items_not_on_k5=dict(unc),
    camera_items_total=sum(sum(cov[t].values()) for t in TYPES[:3]), per_capture=rows)
import math
for name, th in (('t1_repeat_rot', T1_ROT), ('t1_repeat_rot_x2', 2*T1_ROT), ('k5s_max_pass_0.196', 0.19633112108690956),
                 ('k5s_min_gross_0.252', 0.25176818093520587), ('one_deg', 1.0), ('tail_3.9', 3.9)):
    fl = flagged(th, rows)
    sel = {c for c in fl}
    ic = collections.Counter(); icd = collections.Counter()
    for it in items:
        if it['scene'] in sel and it['question_type'] != 'room_size_estimation':
            ic[it['question_type']] += 1; icd[(it['question_type'], ds(it['scene']))] += 1
    res['flags_by_rotation_threshold'][name] = dict(threshold_deg=th, captures=len(fl),
        by_dataset=dict(collections.Counter(ref[k]['dataset'] for k in keys if ref[k]['capture'] in sel)),
        audited=sum(c in audited for c in fl), items=dict(ic), items_by_type_dataset={'%s|%s' % k: v for k, v in icd.items()})
    mde = {}
    for t in TYPES[:4]:
        fl_items = [it for it in items if it['question_type'] == t and it['scene'] in sel]
        byroom = collections.Counter(it['room_key'] for it in fl_items)
        s2 = sum(v*v for v in byroom.values())
        mde[t] = dict(items=len(fl_items), captures=len({it['scene'] for it in fl_items}), rooms=len(byroom),
                      ceiling_points=100*len(fl_items)/150, mde_points_sd1=2.8*100*math.sqrt(s2)/150, mde_points_sd05=1.4*100*math.sqrt(s2)/150)
    res['flags_by_rotation_threshold'][name]['decidability'] = mde
rot = np.array([r['dis_rot_deg'] for r in rows])
res['dis_rot_quantiles'] = dict(min=float(rot.min()), p10=float(np.percentile(rot, 10)), median=float(np.median(rot)), p90=float(np.percentile(rot, 90)), max=float(rot.max()))
res['inputs'] = {str(p): sha(p) for p in (K5/'kit/REFERENCE_K5.json', K5/'ret/g0/50.json', K5/'ret/g1/51.json', K5/'kit/score_k5.py',
    '/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t1/CAMERA_SPLIT.json', '/scratch/jjyeung/orch_n30/lever7/nfa/ref/payload/items/devs1_routed.json',
    '/scratch/jjyeung/orch_n30/lever1_c/arch5/nogt_gt15_20261120.tar', '/scratch/jjyeung/orch_n30/lever1_c/arch6/nogt_arkit7_20261120.tar',
    '/scratch/jjyeung/orch_n30/cont_ops24_c/cap/t1.gz', HERE/'t1rep.py', HERE/'t1rep.json', Path(__file__))}
res['mde_rule'] = ('count-only: ceiling = 100 x flagged items / 150 (largest possible type change); MDE = 2.8 x 100 x sqrt(sum over rooms of '
                   'flagged items squared) / 150 x sd, sd = per-item difference sd assumed 1 (worst case) or 0.5; items in a room treated as fully correlated')
(HERE/'facts_raw.json').write_text(json.dumps(res, indent=1)+'\n')
print(json.dumps({k: v for k, v in res.items() if k not in ('per_capture', 'inputs')}, indent=1))
