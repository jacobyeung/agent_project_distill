"""K5-S: does the tower's default-vs-deterministic disagreement mark captures whose default camera is wrong?

Registered in ROUTED_READER_LEVER_PLAN_20261120.md, section "Tower instability as a sign of tower error (K5-S)".
CPU only; reads banked returns, writes only into this folder.

Reused code (imported, not copied):
- lever6/k5b/kit/score_k5.py: authenticated() L23-33, arms_from() L36-43, split_records() L46-56,
  compare() L71-80 (rot_deg L59-63, trans_m L66-68), pair() L99-106.
- cont_ops24_c/gbuild/gt/v2.py: alignment() L23-47 (the 2026-11-20 audit's rigid fit and pass rule),
  as called by camera_split_round7.py L32 with GT poses from gbuild/out2/GT.json.
- cont_ops24_c/gbuild/gpkg/capture_io.py: Records (the audit's camera loader, camera_split_round7.py L16).
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
K5 = Path('/scratch/jjyeung/orch_n30/lever6/k5b')
GB = Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild')
CAP = GB.parent/'cap'
SPLIT = CAP/'score_t1/CAMERA_SPLIT.json'
GT = GB/'out2/GT.json'
REF = K5/'kit/REFERENCE_K5.json'
DRAWS, SEED = 10000, 0
TAIL_DEG = 3.9
COMPARISONS = (('gross', ('gross',)), ('moderate', ('moderate',)), ('gross+moderate', ('gross', 'moderate')))
DS_NAME = {'arkitscenes': 'ARKit', 'scannet': 'ScanNet', 'scannetppv2': 'ScanNet++'}


def auc(pos, neg):
    """P(random pos > random neg), ties counted half."""
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    if not len(pos) or not len(neg):
        return None
    d = pos[:, None]-neg[None, :]
    return float(((d > 0)+0.5*(d == 0)).mean())


def boot_auc(pos, neg, draws=DRAWS, seed=SEED):
    """Capture bootstrap: resample the pooled captures of both classes with replacement;
    a draw missing either class is undefined and dropped (counted)."""
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    npos, n = len(pos), len(pos)+len(neg)
    if not npos or n == npos:
        return dict(auc=None, ci95=None, defined_draws=0, undefined_draws=draws)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(draws, n))
    counts = np.zeros((draws, n))
    np.add.at(counts, (np.repeat(np.arange(draws), n), idx.ravel()), 1)
    cp, cn = counts[:, :npos], counts[:, npos:]
    d = pos[:, None]-neg[None, :]
    m = (d > 0)+0.5*(d == 0)
    num = np.einsum('di,ij,dj->d', cp, m, cn)
    den = cp.sum(1)*cn.sum(1)
    ok = den > 0
    vals = num[ok]/den[ok]
    return dict(auc=auc(pos, neg), ci95=np.percentile(vals, [2.5, 97.5]).tolist() if ok.any() else None,
                defined_draws=int(ok.sum()), undefined_draws=int((~ok).sum()))


def klass(fit):
    if fit['rotation_max_deg'] > 60:
        return 'gross'
    return 'pass' if fit['accepted'] else 'moderate'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def reproduce_audit(alignment, gt, split):
    """Feed the audit's own T1 cameras (camera_split_round7.py L16-28) to alignment() and compare to CAMERA_SPLIT."""
    from gpkg.capture_io import Records
    cams = {}
    for row in Records(CAP/'t1.gz', CAP/'t1ret/CAPTURE.json'):
        if row['pass_index'] == 0 and row['geometry'] and row['capture'] not in cams:
            cams[row['capture']] = row['geometry']['camera_to_world_metric']
    rows, worst = [], 0.0
    for c in split['captures']:
        x = alignment(cams[c['capture']], gt[c['capture']]['c2w'])
        dev = max(abs(x[k]-c['rigid_fit'][k]) for k in ('translation_rms_m', 'rotation_rms_deg', 'rotation_max_deg'))
        worst = max(worst, dev)
        rows.append(dict(capture=c['capture'], max_abs_dev=dev, accepted_equal=x['accepted'] == c['rigid_fit']['accepted']))
    return dict(captures=len(rows), all_within_1e5=all(r['max_abs_dev'] < 1e-5 for r in rows),
                all_accepted_equal=all(r['accepted_equal'] for r in rows), max_abs_dev=worst)


def main():
    sys.path.insert(0, str(K5/'kit'))
    sys.path.insert(0, str(GB))
    import score_k5 as sk
    from gt.v2 import alignment

    split = json.loads(SPLIT.read_text())
    gt = json.loads(GT.read_text())
    ref_all = json.loads(REF.read_text())
    ref = {c['k']: c for c in ref_all['captures']}
    keys = [c['k'] for c in sorted(ref_all['captures'], key=lambda c: c['position'])]
    n = len(keys)
    results = [sk.authenticated(K5/'ret/g0', 0), sk.authenticated(K5/'ret/g1', 1)]
    arms = sk.arms_from(results)
    p1 = sk.pair(arms, 0, 2, keys, n, ref)   # A1 vs D1 (production order)
    p2 = sk.pair(arms, 1, 3, keys, n, ref)   # A2 vs D2 (replicate)
    assert p1['status'] == p2['status'] == 'complete'
    a1, _ = sk.split_records(arms[0], n)

    gt_prov = split['provenance'].get(str(GT))
    checks = dict(gt_sha_matches_audit_provenance=(gt_prov == sha(GT)), audit_reproduction=reproduce_audit(alignment, gt, split))

    by_cap = {ref[k]['capture']: k for k in keys}
    rows = []
    for c in split['captures']:
        cap = c['capture']
        k = by_cap[cap]
        r = ref[k]
        anchors_equal = r['dump']['source_indices'] == gt[cap]['source_indices']
        assert anchors_equal and len(a1[k]['cm']) == len(gt[cap]['c2w']) == 32
        fit = alignment(a1[k]['cm'], gt[cap]['c2w'])
        rows.append(dict(capture=cap, k=k, dataset=DS_NAME[c['dataset']], position=r['position'],
                         audit_class=klass(c['rigid_fit']),
                         audit_translation_rms_m=c['rigid_fit']['translation_rms_m'],
                         audit_rotation_max_deg=c['rigid_fit']['rotation_max_deg'],
                         a1_class=klass(fit), a1_translation_rms_m=fit['translation_rms_m'],
                         a1_rotation_max_deg=fit['rotation_max_deg'], a1_accepted=fit['accepted'],
                         dis_rot_deg=p1['per_capture'][k]['rotation_deg'], dis_trans_m=p1['per_capture'][k]['translation_m'],
                         rep_rot_deg=p2['per_capture'][k]['rotation_deg'], rep_trans_m=p2['per_capture'][k]['translation_m'],
                         a1_d1_bit=p1['per_capture'][k]['bit']))
    assert len(rows) == 38 and len({r['k'] for r in rows}) == 38

    def sp(x, y):
        v = spearmanr([r[x] for r in rows], [r[y] for r in rows])
        return dict(rho=float(v.statistic), p=float(v.pvalue), n=len(rows))
    spear = {m: {e: sp(m, e) for e in ('a1_translation_rms_m', 'a1_rotation_max_deg', 'audit_translation_rms_m', 'audit_rotation_max_deg')}
             for m in ('dis_rot_deg', 'dis_trans_m')}

    def aucs(metric, cls_key='audit_class'):
        out = {}
        for scope in ('pooled', 'ARKit', 'ScanNet', 'ScanNet++'):
            sel = [r for r in rows if scope == 'pooled' or r['dataset'] == scope]
            neg = [r[metric] for r in sel if r[cls_key] == 'pass']
            out[scope] = {}
            for name, pos_cls in COMPARISONS:
                pos = [r[metric] for r in sel if r[cls_key] in pos_cls]
                e = dict(n_pos=len(pos), n_pass=len(neg))
                if pos and neg:
                    e.update(boot_auc(pos, neg))
                else:
                    e['auc'] = None
                out[scope][name] = e
        return out
    auc_primary = aucs('dis_rot_deg')
    auc_secondary = aucs('dis_trans_m')
    auc_replicate = aucs('rep_rot_deg')
    auc_primary_a1class = aucs('dis_rot_deg', 'a1_class')

    rep = dict(rotation_equal=sum(r['dis_rot_deg'] == r['rep_rot_deg'] for r in rows),
               translation_equal=sum(r['dis_trans_m'] == r['rep_trans_m'] for r in rows),
               max_abs_rot_diff=max(abs(r['dis_rot_deg']-r['rep_rot_deg']) for r in rows),
               max_abs_trans_diff=max(abs(r['dis_trans_m']-r['rep_trans_m']) for r in rows),
               all84_rotation_equal=sum(p1['per_capture'][k]['rotation_deg'] == p2['per_capture'][k]['rotation_deg'] for k in keys),
               all84=n)

    allrot = np.array([p1['per_capture'][k]['rotation_deg'] for k in keys])
    tail = [k for k in keys if p1['per_capture'][k]['rotation_deg'] > TAIL_DEG]
    tail_share = {ds: dict(tail=sum(ref[k]['dataset'] == ds for k in tail), captures=sum(ref[k]['dataset'] == ds for k in keys))
                  for ds in ('ScanNet', 'ScanNet++', 'ARKit')}
    tail_out = dict(threshold_deg=TAIL_DEG, observed_p90_deg=float(np.percentile(allrot, 90)), tail_total=len(tail), all=n,
                    by_dataset=tail_share, tail_in_audit38=sum(k in {r['k'] for r in rows} for k in tail))

    a = auc_primary['pooled']['gross']['auc']
    verdict = 'candidate' if a >= 0.80 else 'closed' if a < 0.65 else 'undecided'
    counts = {c: sum(r['audit_class'] == c for r in rows) for c in ('gross', 'moderate', 'pass')}
    counts_a1 = {c: sum(r['a1_class'] == c for r in rows) for c in ('gross', 'moderate', 'pass')}
    out = dict(schema='k5s-v1', registration='ROUTED_READER_LEVER_PLAN_20261120.md K5-S (registered 2026-11-21T23:27Z)',
               bootstrap=dict(draws=DRAWS, seed=SEED, kind='capture resample of the pooled comparison set; draws lacking a class dropped',
                              interval='percentile 2.5/97.5'),
               auc_convention='P(random positive-class capture has larger disagreement than random pass capture), ties half',
               checks=checks, class_counts_audit=counts, class_counts_a1=counts_a1,
               class_agreement_audit_vs_a1=sum(r['audit_class'] == r['a1_class'] for r in rows),
               per_capture=rows, spearman=spear, auc_primary=auc_primary, auc_secondary=auc_secondary,
               auc_replicate_A2_D2=auc_replicate, auc_primary_on_a1_classes=auc_primary_a1class,
               replicate=rep, tail=tail_out,
               reading=dict(primary_auc_gross_vs_pass_pooled=a, ci95=auc_primary['pooled']['gross']['ci95'], verdict=verdict,
                            rule='>=0.80 candidate; <0.65 closed; else undecided',
                            min_gross_deg=min(r['dis_rot_deg'] for r in rows if r['audit_class'] == 'gross'),
                            max_pass_deg=max(r['dis_rot_deg'] for r in rows if r['audit_class'] == 'pass')),
               inputs={str(p): sha(p) for p in (SPLIT, GT, REF, K5/'ret/g0/50.json', K5/'ret/g1/51.json', K5/'kit/score_k5.py', GB/'gt/v2.py')})
    (HERE/'K5S.json').write_text(json.dumps(out, indent=1, allow_nan=False)+'\n')
    (HERE/'K5S.md').write_text(markdown(out))
    print(json.dumps(out['reading']))


def fmt_auc(e):
    if e.get('auc') is None:
        return 'n/a (%d/%d)' % (e['n_pos'], e['n_pass'])
    lo, hi = e['ci95']
    return '%.3f [%.3f, %.3f] (%d/%d)' % (e['auc'], lo, hi, e['n_pos'], e['n_pass'])


def markdown(o):
    L = ['# K5-S: tower instability against tower error (CPU, banked K5 returns)',
         'Disagreement: A1 vs D1 by score_k5.compare(); rot = largest per-frame rotation diff (deg, primary), trans = largest metric centre diff (m, secondary). '
         'Error: A1 cm vs GT at the 32 anchors by gt/v2.alignment(). Classes: audit (CAMERA_SPLIT.json); A1-class by the same rule, not used for the verdict.', '',
         '| dataset | capture | audit | A1-class | A1 t RMS m | A1 rot max deg | dis rot deg | dis trans m |', '|---|---|---|---|---|---|---|---|']
    for r in sorted(o['per_capture'], key=lambda r: (r['dataset'], r['capture'])):
        L.append('| %s | %s | %s | %s | %.3f | %.2f | %.3g | %.3g |' % (r['dataset'], r['capture'].split('/')[1], r['audit_class'], r['a1_class'],
                 r['a1_translation_rms_m'], r['a1_rotation_max_deg'], r['dis_rot_deg'], r['dis_trans_m']))
    s = o['spearman']
    L += ['', 'Spearman (n=38): rot vs A1 t RMS %.3f (p %.3g), rot vs A1 rot max %.3f (p %.3g); trans vs A1 t RMS %.3f (p %.3g), trans vs A1 rot max %.3f (p %.3g).' % (
        s['dis_rot_deg']['a1_translation_rms_m']['rho'], s['dis_rot_deg']['a1_translation_rms_m']['p'],
        s['dis_rot_deg']['a1_rotation_max_deg']['rho'], s['dis_rot_deg']['a1_rotation_max_deg']['p'],
        s['dis_trans_m']['a1_translation_rms_m']['rho'], s['dis_trans_m']['a1_translation_rms_m']['p'],
        s['dis_trans_m']['a1_rotation_max_deg']['rho'], s['dis_trans_m']['a1_rotation_max_deg']['p']) +
        ' AUC [95%% capture bootstrap, %d draws, seed %d] (n positive/n pass), audit classes:' % (o['bootstrap']['draws'], o['bootstrap']['seed']), '',
        '| metric | scope | gross vs pass | moderate vs pass | gross+moderate vs pass |', '|---|---|---|---|---|']
    for scope in ('pooled', 'ARKit', 'ScanNet', 'ScanNet++'):
        e = o['auc_primary'][scope]
        L.append('| primary rot | %s | %s | %s | %s |' % (scope, fmt_auc(e['gross']), fmt_auc(e['moderate']), fmt_auc(e['gross+moderate'])))
    e = o['auc_secondary']['pooled']
    L.append('| secondary trans | pooled | %s | %s | %s |' % (fmt_auc(e['gross']), fmt_auc(e['moderate']), fmt_auc(e['gross+moderate'])))
    rp, t, c, rd = o['replicate'], o['tail'], o['checks'], o['reading']
    L += ['', 'Replicate A2 vs D2: rotation disagreement equal to A1 vs D1 on %d/%d audit captures (%d/%d of all K5), translation on %d/%d; max diff %.3g deg, %.3g m; replicate primary gross-vs-pass pooled AUC %s.' % (
        rp['rotation_equal'], 38, rp['all84_rotation_equal'], rp['all84'], rp['translation_equal'], 38, rp['max_abs_rot_diff'], rp['max_abs_trans_diff'],
        fmt_auc(o['auc_replicate_A2_D2']['pooled']['gross'])),
        'K5 tail (primary > %.1f deg; observed p90 %.2f deg): %d/%d captures; ' % (t['threshold_deg'], t['observed_p90_deg'], t['tail_total'], t['all']) +
        ', '.join('%s %d/%d' % (ds, v['tail'], v['captures']) for ds, v in t['by_dataset'].items()) + '; %d of the tail are among the 38.' % t['tail_in_audit38'],
        'Classes: audit %s; A1 %s; audit and A1 class agree on %d/38. ' % (o['class_counts_audit'], o['class_counts_a1'], o['class_agreement_audit_vs_a1']) +
        'Fit check: alignment() on the audit\'s own T1 cameras reproduces CAMERA_SPLIT rigid_fit on %d captures (all within 1e-5: %s, accepted equal: %s, max dev %.2g); GT.json sha matches audit provenance: %s.' % (
            c['audit_reproduction']['captures'], c['audit_reproduction']['all_within_1e5'], c['audit_reproduction']['all_accepted_equal'],
            c['audit_reproduction']['max_abs_dev'], c['gt_sha_matches_audit_provenance']),
        '', '**Reading as registered** (primary, gross vs pass, pooled; >=0.80 candidate, <0.65 closed, else undecided): AUC %.3f [%.3f, %.3f] -> **%s**. '
        'With %d gross and %d passing captures the area is fragile: the smallest gross disagreement is %.3f deg against a largest pass of %.3f deg, '
        'and the interval is degenerate because every resample keeps the separation, so it cannot show that fragility.' % (
            rd['primary_auc_gross_vs_pass_pooled'], rd['ci95'][0], rd['ci95'][1], rd['verdict'],
            o['class_counts_audit']['gross'], o['class_counts_audit']['pass'], rd['min_gross_deg'], rd['max_pass_deg'])]
    return '\n'.join(L)+'\n'


if __name__ == '__main__':
    main()
