"""Score authenticated, anchor-bound returns; never turn missing arms into evidence."""
import argparse
import hashlib
import json
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


def decision(rows, complete=True, stub=False):
    if stub:
        return dict(verdict='synthetic', reason='Stub outputs are not experimental evidence')
    if any(r.get('control', {}).get('passed') is False for r in rows):
        return dict(verdict='void', reason='Arm A differs from T1 by more than 0.5 degrees RMS')
    if (not complete or len(rows) != 10 or any(not r.get('control', {}).get('passed') for r in rows)
            or any('B' not in r['arms'] or r['arms']['B']['status'] != 'ok' for r in rows)):
        return dict(verdict='incomplete', reason='The registered comparison requires all ten A/B pairs')
    failing = [r for r in rows if r['group'] == 'failing']
    refs = [r for r in rows if r['group'] == 'reference']
    if len(failing) != 5 or len(refs) != 5:
        raise ValueError('Cohort differs')
    before = float(np.median([r['arms']['A']['relative']['rotation_deg']['rms'] for r in failing]))
    after = float(np.median([r['arms']['B']['relative']['rotation_deg']['rms'] for r in failing]))
    reduction = (before-after)/before if before > 0 else None
    exits = sum(r['arms']['A']['rigid']['classification'] == 'gross' and
                r['arms']['B']['rigid']['classification'] != 'gross' for r in failing)
    rises = [r['arms']['B']['relative']['rotation_deg']['rms']-
             r['arms']['A']['relative']['rotation_deg']['rms'] for r in refs]
    verdict = 'partial'
    if reduction is not None and exits >= 4 and reduction >= .5 and max(rises) <= 2:
        verdict = 'confirm'
    elif reduction is not None and exits <= 1 and reduction < .2:
        verdict = 'refute'
    return dict(verdict=verdict, leaves_gross=exits, median_A_deg=before, median_B_deg=after,
                median_fraction_reduction=reduction, reference_max_rise_deg=max(rises))


def score(data, reference):
    expected = {r['key']:r for r in reference['captures']}
    got = {r['key']:r for r in data['rows']}
    if len(got) != len(data['rows']) or set(got)-set(expected):
        raise ValueError('Duplicate or foreign capture')
    rows = []
    for key, ref in expected.items():
        row = dict(capture=ref['capture'], key=key, group=ref['group'], arms={}, control=None)
        rows.append(row)
        value = got.get(key, dict(arms=[]))
        if len(value['arms']) > 3:
            raise ValueError('Extra arm')
        for a, label in enumerate('ABC'):
            v = value['arms'][a] if a < len(value['arms']) else dict(status='missing')
            row['arms'][label] = dict(status=v['status'])
            if v['status'] != 'ok':
                if v['status'] not in ('unavailable', 'missing'):
                    raise ValueError('Unknown status')
                continue
            plan = ref['arms'][a]
            if plan is None or any(v[k] != plan[k] for k in ('ids', 'sha256', 'slots')):
                raise ValueError('Frame IDs, PNG hashes, or anchor binding differ')
            if v['scale'] != ref['scale'] or v['gravity'] != ref['gravity']:
                raise ValueError('Frozen metric conversion differs')
            all_c = poses(v['c2w'], len(plan['ids']))
            c = all_c[plan['slots']]
            gt = poses(ref['gt'])
            row['arms'][label].update(rigid=rigid(c, gt), relative=relative(c, gt))
            if a == 0:
                control = relative(c, poses(ref['t1']))
                row['control'] = dict(passed=control['rotation_deg']['rms'] <= .5,
                                      relative_rotation_rms_deg=control['rotation_deg']['rms'])
    return dict(schema='tower2x-score-v1', rows=rows,
                **decision(rows, data['complete'], data['stub']),
                interpretation='Conditional on the recorded GT/RGB binding; no scale fit. Scale and gravity are frozen T1 values.')


def render(result):
    lines = [f"Verdict: **{result['verdict']}**.", result.get('reason', ''), result['interpretation'], '',
             '| Capture | Group | Control RMS ° | Arm | Class/status | Rigid trans RMS m | Rigid rot max ° | Relative rot RMS ° | Relative trans RMS m |',
             '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in result['rows']:
        control = f"{r['control']['relative_rotation_rms_deg']:.4f}" if r['control'] else 'missing'
        for label, a in r['arms'].items():
            values = [r['capture'], r['group'], control, label, a['status'], '—', '—', '—', '—']
            if a['status'] == 'ok':
                values[4:] = [a['rigid']['classification'], f"{a['rigid']['translation_rms_m']:.5f}",
                              f"{a['rigid']['rotation_max_deg']:.4f}", f"{a['relative']['rotation_deg']['rms']:.4f}",
                              f"{a['relative']['translation_m']['rms']:.5f}"]
            lines.append('| '+' | '.join(values)+' |')
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
    for name, raw in [('TOWER2X.json', json.dumps(result, indent=2, allow_nan=False)+'\n'), ('TOWER2X.md', render(result))]:
        with (a.out/name).open('x') as f:
            f.write(raw)
    print(result['verdict'])


if __name__ == '__main__':
    main()
