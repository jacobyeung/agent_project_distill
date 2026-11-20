"""Score authenticated, anchor-bound returns; never turn missing arms into evidence."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def poses(value, n=32):
    a = np.asarray(value, float)
    if (a.shape != (n, 4, 4) or not np.isfinite(a).all()
            or not np.allclose(a[:, 3], [0, 0, 0, 1], atol=1e-6)
            or not np.allclose(a[:, :3, :3] @ a[:, :3, :3].transpose(0, 2, 1), np.eye(3), atol=1e-5)
            or not np.allclose(np.linalg.det(a[:, :3, :3]), 1, atol=1e-5)):
        raise ValueError('Invalid SE(3) cameras')
    return a


def angles(r):
    return np.degrees(np.arccos(np.clip((np.trace(r, axis1=-2, axis2=-1)-1)/2, -1, 1)))


def relative(a, b):
    i, j = np.triu_indices(len(a), 1)
    ar, br = a[:, :3, :3], b[:, :3, :3]
    ra, rb = ar[i].transpose(0, 2, 1) @ ar[j], br[i].transpose(0, 2, 1) @ br[j]
    da, db = a[j, :3, 3]-a[i, :3, 3], b[j, :3, 3]-b[i, :3, 3]
    ta, tb = np.einsum('ni,nij->nj', da, ar[i]), np.einsum('ni,nij->nj', db, br[i])
    values = dict(rotation_deg=angles(ra @ rb.transpose(0, 2, 1)),
                  translation_m=np.linalg.norm(ta-tb, axis=1),
                  baseline_length_difference_m=np.abs(np.linalg.norm(da, axis=1)-np.linalg.norm(db, axis=1)))
    return dict(pairs=len(i), **{k:dict(rms=float(np.sqrt(np.mean(v*v))), median=float(np.median(v)),
                max=float(v.max()), residuals=v.tolist()) for k, v in values.items()})


def rigid(a, b):
    x, y = a[:, :3, 3], b[:, :3, 3]
    xc, yc = x-x.mean(0), y-y.mean(0)
    u, _, vt = np.linalg.svd(xc.T @ yc)
    r = vt.T @ np.diag([1., 1., np.linalg.det(vt.T @ u.T)]) @ u.T
    t = y.mean(0)-r @ x.mean(0)
    e = np.linalg.norm(x @ r.T+t-y, axis=1)
    q = angles((r @ a[:, :3, :3]) @ b[:, :3, :3].transpose(0, 2, 1))
    rank = int(np.linalg.matrix_rank(xc, tol=1e-8))
    rms = float(np.sqrt(np.mean(e*e)))
    accepted = rank >= 2 and rms <= .1 and float(q.max()) <= 5
    return dict(fit_scale=False, translation_rms_m=rms, translation_residual_m=e.tolist(),
                rotation_rms_deg=float(np.sqrt(np.mean(q*q))), rotation_max_deg=float(q.max()),
                rotation_residual_deg=q.tolist(), center_rank=rank, accepted=accepted,
                rotation=r.tolist(), translation=t.tolist(),
                classification='pass' if accepted else 'gross' if q.max() > 60 else 'moderate')


def decision(rows, complete=True, stub=False, label='B', baseline='A', required=10):
    if stub:
        return dict(verdict='synthetic', reason='Stub outputs are not experimental evidence')
    controls = [r.get('control') for r in rows]
    failures = sum(c is not None and not c['passed'] for c in controls)
    if failures > 10-required:
        return dict(verdict='void', reason="The decode, not coverage, moved the cameras: fewer than eight of ten A' controls can meet 1.0 degree RMS" if baseline=="A'" else 'Arm A differs from T1 by more than 0.5 degrees RMS')
    if (len(rows) != 10 or any(c is None for c in controls)
            or any(r['arms'].get(baseline, {}).get('status') != 'ok' or
                   r['arms'].get(label, {}).get('status') != 'ok' for r in rows)):
        return dict(verdict='incomplete', reason='The registered comparison requires all ten baseline/comparison pairs and controls')
    failing = [r for r in rows if r['group'] == 'failing']
    refs = [r for r in rows if r['group'] == 'reference']
    if len(failing) != 5 or len(refs) != 5:
        raise ValueError('Cohort differs')
    before = float(np.median([r['arms'][baseline]['relative']['rotation_deg']['rms'] for r in failing]))
    after = float(np.median([r['arms'][label]['relative']['rotation_deg']['rms'] for r in failing]))
    reduction = (before-after)/before if before > 0 else None
    exits = sum(r['arms'][baseline]['similarity']['classification'] == 'gross' and
                r['arms'][label]['similarity']['classification'] != 'gross' for r in failing)
    rises = [r['arms'][label]['relative']['rotation_deg']['rms']-
             r['arms'][baseline]['relative']['rotation_deg']['rms'] for r in refs]
    verdict = 'partial'
    if reduction is not None and exits >= 4 and reduction >= .5 and max(rises) <= 2:
        verdict = 'confirm'
    elif reduction is not None and exits <= 1 and reduction < .2:
        verdict = 'refute'
    return dict(verdict=verdict, leaves_gross=exits, baseline_arm=baseline, median_baseline_deg=before, comparison_arm=label, median_comparison_deg=after,
                median_fraction_reduction=reduction, reference_max_rise_deg=max(rises))


def score(data, reference):
    baseline=reference.get('baseline','A')
    limit=reference.get('control_limit_deg',.5)
    required=reference.get('control_required',10)
    expected = {r['key']:r for r in reference['captures']}
    got = {r['key']:r for r in data['rows']}
    if len(got) != len(data['rows']) or set(got)-set(expected):
        raise ValueError('Duplicate or foreign capture')
    rows = []
    for key, ref in expected.items():
        row = dict(capture=ref['capture'], key=key, group=ref['group'], arms={}, control=None)
        rows.append(row)
        value = got.get(key, dict(arms=[]))
        if len(value['arms']) > len(ref['arms']):
            raise ValueError('Extra arm')
        for a, label in enumerate(reference.get('labels', ['A','B','C'])):
            v = value['arms'][a] if a < len(value['arms']) else dict(status='missing')
            row['arms'][label] = dict(status=v['status'])
            if v['status'] != 'ok':
                if v['status'] not in ('unavailable', 'missing', 'budget', 'error'):
                    raise ValueError('Unknown status')
                continue
            plan = ref['arms'][a]
            if plan is None or any(v[k] != plan[k] for k in ('ids', 'sha256', 'slots')):
                raise ValueError('Frame IDs, PNG hashes, or anchor binding differ')
            if reference.get('decode_recording'):
                hashes = v.get('raw_sha256', [])
                matches = v.get('raw_matches', [])
                versions = v.get('decode_versions', [])
                if (len(hashes) != len(plan['ids']) or
                        any(not isinstance(h, str) or not re.fullmatch('[a-f0-9]{64}', h) for h in hashes) or
                        len(matches) != len(hashes) or any(type(x) is not bool for x in matches) or
                        matches != [h == expected for h, expected in zip(hashes, plan['raw_sha256'])] or
                        type(v.get('raw_match_count')) is not int or v['raw_match_count'] != sum(matches) or
                        len(versions) != len(hashes) or any(not isinstance(x, dict) or
                            set(x) != {'cv2', 'PIL', 'numpy'} or
                            any(not isinstance(y, str) or not y or len(y) > 100 for y in x.values()) for x in versions)):
                    raise ValueError('Invalid decode records')
                row['arms'][label].update(raw_sha256=hashes,raw_matches=matches,
                    raw_match_count=sum(matches),decode_versions=versions)
            elif v['raw_sha256'] != plan['raw_sha256']:
                raise ValueError('Raw hashes differ')
            if v['scale'] != ref['scale'] or v['gravity'] != ref['gravity']:
                raise ValueError('Frozen metric conversion differs')
            all_c = poses(v['c2w'], len(plan['ids']))
            c = all_c[plan['slots']]
            gt = poses(ref['gt'])
            row['arms'][label].update(rigid=rigid(c, gt), similarity=similarity(c, gt),
                                     relative=relative(c, gt), gravity=gravity(c, gt, ref['gravity']))
            if label == baseline:
                control = relative(c, poses(ref['t1']))
                row['control'] = dict(passed=control['rotation_deg']['rms'] <= limit,
                                      relative_rotation_rms_deg=control['rotation_deg']['rms'], threshold_deg=limit)
        if row['arms'][baseline]['status'] == 'ok':
            base = row['arms'][baseline]['similarity']['scale']
            for arm in row['arms'].values():
                if arm['status'] == 'ok':
                    scale=arm['similarity']['scale']
                    arm['similarity']['scale_relative_to_baseline'] = scale/base if base and scale is not None else None
                    if baseline == 'A':arm['similarity']['scale_relative_to_A'] = arm['similarity']['scale_relative_to_baseline']
    if reference.get('decode_recording'):
        count = sum(a.get('raw_match_count', 0) for r in data['rows'] for a in r['arms'])
        total = sum(len(a.get('raw_sha256', [])) for r in data['rows'] for a in r['arms'])
        if data.get('raw_match_count') != count or data.get('raw_frame_count') != total:
            raise ValueError('Decode totals differ')
    decisions = {label:(decision(rows, data['complete'], data['stub'], label, baseline, required)
                       if label in reference.get('active_comparisons', ['B','C'])
                       else dict(verdict='skipped', reason='Arm dropped from the requested experiment'))
                 for label in ('B','C')}
    return dict(schema='tower2x-b-score-v2', baseline=baseline, rows=rows, decisions=decisions,
                decode_control=dict(passed_captures=sum(bool((r['control'] or {}).get('passed')) for r in rows),
                    evaluated_captures=sum(r['control'] is not None for r in rows),required_captures=required,threshold_deg=limit),
                verdict=decisions['B']['verdict'],
                interpretation='GT conclusions remain conditional on REPORT9 binding. Metric scale and gravity are frozen T1 values. Similarity fits determine class; rigid fits retain the round-5 rule. Each arm comparison is complete independently.')


def similarity(a, b):
    x,y = a[:,:3,3],b[:,:3,3]
    xc,yc = x-x.mean(0),y-y.mean(0)
    u,d,vt = np.linalg.svd(xc.T@yc)
    sign = np.array([1.,1.,np.linalg.det(vt.T@u.T)])
    r = vt.T@np.diag(sign)@u.T
    variance = float(np.sum(xc*xc))
    scale = float(np.sum(d*sign)/variance) if variance > 1e-16 else None
    t = y.mean(0)-(scale if scale is not None else 1.)*r@x.mean(0)
    e = np.linalg.norm((scale if scale is not None else 1.)*x@r.T+t-y,axis=1)
    q = angles((r@a[:,:3,:3])@b[:,:3,:3].transpose(0,2,1))
    rank = int(np.linalg.matrix_rank(xc,tol=1e-8))
    rms = float(np.sqrt(np.mean(e*e)))
    passed = rank>=2 and scale is not None and scale>0 and rms<=.1 and q.max()<=5
    return dict(fit_scale=True,scale=scale,scale_relative_to_baseline=None,center_rank=rank,
                translation_rms_m=rms,translation_residual_m=e.tolist(),rotation_residual_deg=q.tolist(),
                rotation_rms_deg=float(np.sqrt(np.mean(q*q))),rotation_max_deg=float(q.max()),
                rotation=r.tolist(),translation=t.tolist(),accepted=bool(passed),
                classification='pass' if passed else 'gross' if q.max()>60 else 'moderate')


def gravity(a, b, origin_up):
    r = a[:,:3,:3]
    up = np.asarray(origin_up,float);up = up/np.linalg.norm(up)
    # R_i^T R_0 transports T1's first-camera up into camera i.
    pred = r.transpose(0,2,1)@r[0]@up
    target = b[:,:3,:3].transpose(0,2,1)@np.array([0.,0.,1.])
    q = np.degrees(np.arccos(np.clip(np.sum(pred*target,axis=1),-1.,1.)))
    return dict(mean_deg=float(q.mean()),max_deg=float(q.max()),residual_deg=q.tolist(),
                predicted_up=pred.tolist(),gt_up=target.tolist())


def render(result):
    lines = [f"B verdict: **{result['decisions']['B']['verdict']}**; C verdict: **{result['decisions']['C']['verdict']}**.",
             result['interpretation'], '',
             f"| Capture | Arm | Rigid class | Similarity class | Sim scale | Scale/{result['baseline']} | Rigid trans RMS m | Sim trans RMS m | Rigid rot max ° | Sim rot max ° | Relative rot RMS ° | Gravity mean / max ° |",
             '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    def fmt(x):
        return 'undefined' if x is None else f'{x:.5f}'
    for row in result['rows']:
        for label,a in row['arms'].items():
            if a['status']!='ok':
                lines.append('| '+' | '.join([row['capture'],label,a['status']]+['—']*9)+' |')
                continue
            r,s,g = a['rigid'],a['similarity'],a['gravity']
            values = [row['capture'],label,r['classification'],s['classification'],fmt(s['scale']),fmt(s['scale_relative_to_baseline']),
                      fmt(r['translation_rms_m']),fmt(s['translation_rms_m']),fmt(r['rotation_max_deg']),fmt(s['rotation_max_deg']),
                      fmt(a['relative']['rotation_deg']['rms']),fmt(g['mean_deg'])+' / '+fmt(g['max_deg'])]
            lines.append('| '+' | '.join(values)+' |')
    lines += ['', '| Capture | Decode control RMS ° | Pass |', '| --- | --- | --- |']
    for row in result['rows']:
        c=row['control']
        lines.append('| '+row['capture']+' | '+(fmt(c['relative_rotation_rms_deg'])+' | '+str(c['passed']) if c else 'missing | —')+' |')
    d=result['decode_control']
    lines.append(f"\nDecode controls: {d['passed_captures']}/{d['evaluated_captures']} pass; require {d['required_captures']}/10 at ≤{d['threshold_deg']}°.")
    for row in result['rows']:
        for label, arm in row['arms'].items():
            if 'raw_match_count' in arm:
                lines.append(f"{row['capture']} {label}: {arm['raw_match_count']}/{len(arm['raw_sha256'])} raw hashes match Trinity.")
    reason=result['decisions']['B'].get('reason')
    if reason:lines.append(reason)
    return '\n'.join(lines)+'\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--return', dest='returned', type=Path, required=True)
    ap.add_argument('--receipt', type=Path, required=True)
    ap.add_argument('--reference', type=Path, default=Path(__file__).with_name('REFERENCE.json'))
    ap.add_argument('--out', type=Path, default=Path(__file__).parent)
    a = ap.parse_args()
    data, receipt, ref = [json.loads(p.read_text()) for p in (a.returned, a.receipt, a.reference)]
    if (a.returned.stat().st_size >= 5_000_000 or receipt['sha256'] != sha(a.returned)
            or receipt['bytes'] != a.returned.stat().st_size or data['token'] != ref['token']
            or receipt['token'] != ref['token'] or receipt['complete'] != data['complete']
            or receipt['stub'] != data['stub'] or receipt['input_sha256'] != ref['input_sha256']):
        raise ValueError('Return receipt differs')
    result = score(data, ref)
    result['provenance'] = dict(return_sha256=sha(a.returned), receipt_sha256=sha(a.receipt), reference_sha256=sha(a.reference))
    a.out.mkdir(exist_ok=True, parents=True)
    for name, raw in [('TOWER2X_B.json', json.dumps(result, indent=2, allow_nan=False)+'\n'), ('TOWER2X_B.md', render(result))]:
        with (a.out/name).open('x') as f:
            f.write(raw)
    print(result['verdict'])


if __name__ == '__main__':
    main()
