"""STAB threshold tau (DESIGN_STAB.md, Threshold). Uses no score: K5 tower cameras and GT cameras only.

Disagreement: A1 vs D1, largest per-frame rotation difference (score_k5.pair(arms, 0, 2)).
Fit set: K5 captures outside the 38 audited ones with GT cameras at the 32 anchors (21 rank-5 NOGT NPZs, 41254810
left out, plus 19 camera T1-GT NPZs); never any of the 38.
Label: gross = A1's rigid-fit rotation maximum against GT > 60 deg (gt/v2.alignment).
Rule: tau maximises Youden's J = TPR - FPR (flag = disagreement > tau); cuts at the geometric mean of two adjacent
distinct sorted disagreements; a tie goes to the larger tau; fewer than 3 gross or 3 non-gross: void fit, tau = 3.9.
"""
import collections
import io
import json
import sys
import math
import tarfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script directory
import common as C  # noqa: E402

MIN_CLASS = 3
GROSS_DEG = 60.0
REG_FIT = dict(captures=40, by_dataset={'ScanNet': 21, 'ScanNet++': 13, 'ARKit': 6}, nogt=21, camgt=19)


def youden(values, gross, void_tau=C.VOID_TAU, min_class=MIN_CLASS):
    """values: disagreements; gross: bools. Returns the fit record."""
    v = np.asarray(values, float)
    g = np.asarray(gross, bool)
    npos, nneg = int(g.sum()), int((~g).sum())
    rec = dict(n=len(v), gross=npos, non_gross=nneg, min_class=min_class)
    if npos < min_class or nneg < min_class:
        return dict(rec, void=True, tau=void_tau, J=None, cuts=[])
    u = np.unique(v)
    cuts = []
    for a, b in zip(u[:-1], u[1:]):
        t = math.sqrt(a*b)
        f = v > t
        tpr = float((f & g).sum())/npos
        fpr = float((f & ~g).sum())/nneg
        cuts.append(dict(tau=t, tpr=tpr, fpr=fpr, J=tpr-fpr, flagged=int(f.sum())))
    if not cuts:
        return dict(rec, void=True, tau=void_tau, J=None, cuts=[], reason='all disagreements equal')
    best = max(c['J'] for c in cuts)
    tied = [c for c in cuts if abs(c['J']-best) <= 1e-12]
    pick = max(tied, key=lambda c: c['tau'])          # tie -> larger tau, flags fewer
    return dict(rec, void=False, tau=pick['tau'], J=pick['J'], tpr=pick['tpr'], fpr=pick['fpr'],
                tied_cuts=len(tied), cuts=cuts)


def klass(fit):
    if fit['rotation_max_deg'] > GROSS_DEG:
        return 'gross'
    return 'pass' if fit['accepted'] else 'moderate'


def npz_name(member):
    nm = Path(member).name[:-4]
    return nm.replace('__', '/') if '__' in nm else 'arkitscenes/'+nm


def load_gt():
    """capture -> dict(c2w, frame_indices, valid, source, sha256)."""
    nogt, camgt = {}, {}
    for t in ('nogt_tar5', 'nogt_tar6'):
        with tarfile.open(C.REG[t][0]) as tf:
            for m in tf.getmembers():
                if m.name.endswith('.npz'):
                    raw = tf.extractfile(m).read()
                    with np.load(io.BytesIO(raw), allow_pickle=False) as z:
                        nogt[npz_name(m.name)] = dict(c2w=np.asarray(z['c2w'], float), frame_indices=z['frame_indices'].tolist(),
                                                      valid=z['valid'].tolist(), source='%s:%s' % (t, m.name),
                                                      sha256=__import__('hashlib').sha256(raw).hexdigest())
    for p in sorted(C.CAMGT_DIR.glob('*.npz')):
        with np.load(p, allow_pickle=False) as z:
            camgt[npz_name(p.name)] = dict(c2w=np.asarray(z['c2w'], float), frame_indices=z['frame_indices'].tolist(),
                                           valid=z['valid'].tolist(), source=str(p), sha256=C.sha(p))
    return nogt, camgt


def k5_disagreement():
    C.imports()
    import score_k5 as sk
    ref_all = json.loads(C.REG['k5_reference'][0].read_text())
    ref = {c['k']: c for c in ref_all['captures']}
    keys = [c['k'] for c in sorted(ref_all['captures'], key=lambda c: c['position'])]
    n = len(keys)
    arms = sk.arms_from([sk.authenticated(C.K5/'ret/g0', 0), sk.authenticated(C.K5/'ret/g1', 1)])
    p = sk.pair(arms, 0, 2, keys, n, ref)
    if p['status'] != 'complete':
        raise ValueError('A1 vs D1 incomplete')
    a1, _ = sk.split_records(arms[0], n)
    caps = {}
    for k in keys:
        r = ref[k]
        caps[r['capture']] = dict(k=k, dataset=r['dataset'], position=r['position'], rank1=r['rank1'],
                                  dump_indices=(r.get('dump') or {}).get('source_indices'),
                                  dis_rot_deg=p['per_capture'][k]['rotation_deg'], dis_trans_m=p['per_capture'][k]['translation_m'],
                                  a1_cm=a1[k]['cm'])
    return caps


def flag_counts(items, flagged):
    """Counts only: flagged items, captures, rooms and the ceiling per type."""
    out = {}
    for kind in C.TYPES:
        fl = [it for it in items.values() if it['question_type'] == kind and it['scene'] in flagged]
        total = sum(it['question_type'] == kind for it in items.values())
        rooms = collections.Counter(it['room_key'] for it in fl)
        out[kind] = dict(items=len(fl), of=total, captures=len({it['scene'] for it in fl}), rooms=len(rooms),
                         ceiling_points=100.0*len(fl)/total,
                         by_dataset=dict(collections.Counter(C.ds_of(it['scene']) for it in fl)))
    return out


def main():
    inputs = C.verify(['k5_reference', 'k5_g0', 'k5_g1', 'score_k5', 'gt_v2', 'camera_split', 'k5s', 'nogt_tar5', 'nogt_tar6', 'items'])
    C.imports()
    from gt.v2 import alignment
    caps = k5_disagreement()
    split = json.loads(C.REG['camera_split'][0].read_text())
    audit = {c['capture']: klass(c['rigid_fit']) for c in split['captures']}
    k5s = {r['capture']: r for r in json.loads(C.REG['k5s'][0].read_text())['per_capture']}
    if set(audit) != set(k5s) or len(audit) != 38 or not set(audit) <= set(caps):
        raise ValueError('audited 38 do not join')
    for c, r in k5s.items():
        if r['dis_rot_deg'] != caps[c]['dis_rot_deg']:
            raise ValueError('disagreement differs from K5S.json for %s' % c)
    items = C.load_items()
    item_idx = collections.defaultdict(list)
    for it in items.values():
        item_idx[it['scene']].append(it['source_frame_indices'])
    nogt, camgt = load_gt()

    fit = []
    for cap in sorted(caps):
        if cap in audit or cap in C.EXCLUDED_FIT:
            continue
        g = nogt.get(cap) or camgt.get(cap)
        if g is None:
            continue
        src = 'nogt' if cap in nogt else 'camgt'
        c = caps[cap]
        bind = []
        if c['dump_indices'] is not None:
            if c['dump_indices'] != g['frame_indices']:
                raise ValueError('GT anchors differ from K5 dump: %s' % cap)
            bind.append('k5_dump')
        idx = item_idx.get(cap, [])
        if idx:
            if any(x != g['frame_indices'] for x in idx):
                raise ValueError('GT anchors differ from item frames: %s' % cap)
            bind.append('items(%d)' % len(idx))
        if not bind:
            raise ValueError('GT anchors bind to nothing: %s' % cap)
        both = None
        if cap in nogt and cap in camgt:
            both = bool(np.array_equal(nogt[cap]['c2w'], camgt[cap]['c2w']) and nogt[cap]['frame_indices'] == camgt[cap]['frame_indices'])
        if not all(g['valid']) or len(g['c2w']) != 32 or len(c['a1_cm']) != 32:
            raise ValueError('GT or A1 not 32 valid anchors: %s' % cap)
        a = alignment(c['a1_cm'], g['c2w'])
        fit.append(dict(capture=cap, dataset=c['dataset'], source=src, gt_file=g['source'], gt_sha256=g['sha256'], binding=bind,
                        also_in_other_source_equal=both, a1_rotation_max_deg=a['rotation_max_deg'],
                        gross=a['rotation_max_deg'] > GROSS_DEG, dis_rot_deg=c['dis_rot_deg'], metric_scale=bool(c['rank1'])))
    counts = dict(captures=len(fit), by_dataset=dict(collections.Counter(f['dataset'] for f in fit)),
                  nogt=sum(f['source'] == 'nogt' for f in fit), camgt=sum(f['source'] == 'camgt' for f in fit))
    if counts != REG_FIT:
        raise ValueError('fit set differs from the registered one: %s' % counts)
    if set(f['capture'] for f in fit) & set(audit):
        raise AssertionError('fit set touches the 38')
    res = youden([f['dis_rot_deg'] for f in fit], [f['gross'] for f in fit])
    tau = res['tau']
    counts['gross_by_dataset'] = dict(collections.Counter(f['dataset'] for f in fit if f['gross']))

    def oos(cls_of):
        out = {}
        for cname in ('gross', 'moderate', 'pass'):
            sel = [c for c in audit if cls_of(c) == cname]
            out[cname] = dict(captures=len(sel), flagged=sum(caps[c]['dis_rot_deg'] > tau for c in sel))
        return out
    flagged = sorted(c for c in caps if caps[c]['dis_rot_deg'] > tau)
    fragile = sorted(c for c in caps if tau/2 <= caps[c]['dis_rot_deg'] <= 2*tau)
    flipped = sorted((set(flagged) - set(fragile)) | (set(fragile) - set(flagged)))
    out = dict(schema='stab-tau-v1', registration='DESIGN_STAB.md, Threshold (lane lever7, 2026-11-21)',
               note='no score, accuracy or paired difference was computed',
               tau_deg=tau, void_fit=res['void'], rule=__doc__.split('Rule: ')[1].strip(), fit=dict(counts, **{k: v for k, v in res.items() if k != 'cuts'}),
               cuts=res['cuts'], fit_captures=fit,
               out_of_sample_38=dict(audit_classes=oos(lambda c: audit[c]),
                                     a1_classes_with_translation=oos(lambda c: k5s[c]['a1_class']),
                                     note='a1_classes_with_translation: classes from A1\'s own rigid fit (translation RMS enters pass/moderate), K5S.json'),
               flags=dict(captures=len(flagged), by_dataset=dict(collections.Counter(caps[c]['dataset'] for c in flagged)),
                          audited=sum(c in audit for c in flagged), list=flagged, items=flag_counts(items, set(flagged))),
               fragile=dict(rule='tau/2 <= disagreement <= 2 tau', captures=len(fragile), list=fragile,
                            flipped_flags=dict(captures=len(flipped), list=flipped, items=flag_counts(items, set(flipped)))),
               per_capture={c: dict(dis_rot_deg=v['dis_rot_deg'], dataset=v['dataset'], audited=c in audit, flagged=v['dis_rot_deg'] > tau,
                                    fragile=c in fragile) for c, v in sorted(caps.items())},
               inputs=inputs)
    C.TAU_JSON.write_text(json.dumps(out, indent=1, allow_nan=False)+'\n')
    print(json.dumps(dict(tau_deg=tau, void_fit=res['void'], fit={k: v for k, v in out['fit'].items()}, out_of_sample_38=out['out_of_sample_38'],
                          flags={k: out['flags'][k] for k in ('captures', 'audited', 'by_dataset')},
                          items={k: v['items'] for k, v in out['flags']['items'].items()}, fragile=len(fragile)), indent=1))


if __name__ == '__main__':
    main()
