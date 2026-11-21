"""Score the K4 return: K3d per-arm rules, noise floors, and the pre-registered coverage verdict."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import numpy as np

_spec = importlib.util.spec_from_file_location('k3d_score', Path(__file__).with_name('k3d_score.py'))
K = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(K)

LABELS = ['A', 'A2', "A'", "B'", "C'", 'Bm', 'Cm']
RISE_DEG = 2.0


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_versions(x):
    if (not isinstance(x, dict) or set(x) != {'cv2', 'PIL', 'numpy'}
            or any(not isinstance(y, str) or not y or len(y) > 100 for y in x.values())):
        raise ValueError('Invalid decode versions')


def validate(v, plan, ref):
    if any(v[k] != plan[k] for k in ('ids', 'sha256', 'slots')):
        raise ValueError('Frame IDs, PNG hashes, or anchor binding differ')
    hashes, matches = v.get('raw_sha256', []), v.get('raw_matches', [])
    if (len(hashes) != len(plan['ids'])
            or any(not isinstance(h, str) or not re.fullmatch('[a-f0-9]{64}', h) for h in hashes)
            or len(matches) != len(hashes) or any(type(x) is not bool for x in matches)
            or matches != [h == e for h, e in zip(hashes, plan['raw_sha256'])]
            or type(v.get('raw_match_count')) is not int or v['raw_match_count'] != sum(matches)):
        raise ValueError('Invalid decode records')
    versions = v.get('decode_versions')
    for x in (versions if isinstance(versions, list) else [versions]):
        check_versions(x)
    if isinstance(versions, list) and len(versions) != len(hashes):
        raise ValueError('Invalid decode versions')
    if v['scale'] != ref['scale'] or v['gravity'] != ref['gravity']:
        raise ValueError('Frozen metric conversion differs')
    return K.poses(v['c2w'], len(plan['ids']))[plan['slots']]


def pair(a, b):
    rel = K.relative(a, b)
    d = np.linalg.norm(a[:, :3, 3]-b[:, :3, 3], axis=1)
    return dict(relative_rotation_rms_deg=rel['rotation_deg']['rms'], relative_rotation_max_deg=rel['rotation_deg']['max'],
                relative_translation_rms_m=rel['translation_m']['rms'],
                center_rms_m=float(np.sqrt(np.mean(d*d))), center_max_m=float(d.max()))


def rr(row, label):
    return row['arms'][label]['relative']['rotation_deg']['rms']


def sim_class(row, label):
    return row['arms'][label]['similarity']['classification']


def verdict(rows, baseline, arms, stub):
    if stub:
        return dict(verdict='synthetic', reason='Stub outputs are not experimental evidence')
    if len(rows) != 10 or any(a['status'] != 'ok' for r in rows for a in r['arms'].values()) or any(r['floor_deg'] is None for r in rows):
        return dict(verdict='incomplete', reason='The verdict requires every arm returned for every capture')
    failing = [r for r in rows if r['group'] == 'failing']
    refs = [r for r in rows if r['group'] == 'reference']
    if len(failing) != 5 or len(refs) != 5:
        raise ValueError('Cohort differs')
    detail, repaired, violations = {}, {}, []
    for x in arms:
        repaired[x] = []
        for r in failing:
            drop = rr(r, baseline)-rr(r, x)
            ok = sim_class(r, baseline) == 'gross' and sim_class(r, x) != 'gross' and drop > r['floor_deg']
            detail.setdefault(r['capture'], {})[x] = dict(gross_at_baseline=sim_class(r, baseline) == 'gross',
                class_at_arm=sim_class(r, x), drop_deg=drop, floor_deg=r['floor_deg'], repaired=ok)
            if ok:
                repaired[x].append(r['capture'])
        for r in refs:
            rise = rr(r, x)-rr(r, baseline)
            bad = rise > RISE_DEG+r['floor_deg']
            detail.setdefault(r['capture'], {})[x] = dict(rise_deg=rise, limit_deg=RISE_DEG+r['floor_deg'], violates=bad)
            if bad:
                violations.append([r['capture'], x])
    union = sorted(set(c for x in arms for c in repaired[x]))
    if len(union) >= 3 and not violations:
        out = 'confirm'
    elif all(len(repaired[x]) <= 1 for x in arms):
        out = 'refute'
    else:
        out = 'inconclusive'
    return dict(verdict=out, baseline=baseline, arms=list(arms), repaired={x: repaired[x] for x in arms},
                repaired_any=union, gross_at_baseline=sum(sim_class(r, baseline) == 'gross' for r in failing),
                reference_violations=violations, detail=detail)


def score(data, reference, prior=None):
    labels = reference['labels']
    if labels != LABELS:
        raise ValueError('Labels differ')
    expected = {r['key']: r for r in reference['captures']}
    got = {r['key']: r for r in data['rows']}
    if len(got) != len(data['rows']) or set(got)-set(expected):
        raise ValueError('Duplicate or foreign capture')
    prior_rows = {r['key']: r for r in prior['rows']} if prior else {}
    rows = []
    for key, ref in expected.items():
        row = dict(capture=ref['capture'], key=key, group=ref['group'], arms={}, compare={}, floor_deg=None)
        rows.append(row)
        value = got.get(key, dict(arms=[]))
        if len(value['arms']) > len(labels):
            raise ValueError('Extra arm')
        cams = {}
        gt = K.poses(ref['gt'])
        for a, label in enumerate(labels):
            v = value['arms'][a] if a < len(value['arms']) else dict(status='missing')
            row['arms'][label] = dict(status=v['status'])
            if v['status'] != 'ok':
                if v['status'] not in ('unavailable', 'missing', 'budget', 'error'):
                    raise ValueError('Unknown status')
                continue
            c = validate(v, ref['arms'][a], ref)
            cams[label] = c
            row['arms'][label].update(rigid=K.rigid(c, gt), similarity=K.similarity(c, gt), relative=K.relative(c, gt),
                                      gravity=K.gravity(c, gt, ref['gravity']), raw_match_count=v['raw_match_count'],
                                      frames=len(v['ids']), seconds=v.get('seconds'))
        if 'A' in cams:
            row['compare']['A_vs_T1'] = pair(cams['A'], K.poses(ref['t1']))
            base = row['arms']['A']['similarity']['scale']
            for arm in row['arms'].values():
                if arm['status'] == 'ok':
                    s = arm['similarity']['scale']
                    arm['similarity']['scale_relative_to_A'] = s/base if base and s is not None else None
        if "A'" in cams:
            row['compare']["A'_vs_T1"] = pair(cams["A'"], K.poses(ref['t1']))
        for other in ('A2', "A'"):
            if 'A' in cams and other in cams:
                row['compare']['A_vs_'+other] = pair(cams['A'], cams[other])
        if all(x in cams for x in ('A', 'A2', "A'")):
            row['floor_deg'] = max(abs(rr(row, 'A')-rr(row, 'A2')), abs(rr(row, 'A')-rr(row, "A'")))
        if key in prior_rows:
            for mine, theirs in (("A'", 0), ("B'", 1)):
                p = prior_rows[key]['arms'][theirs] if theirs < len(prior_rows[key]['arms']) else {}
                if mine in cams and p.get('status') == 'ok':
                    if p['ids'] != ref['arms'][LABELS.index(mine)]['ids']:
                        raise ValueError('Prior frame IDs differ')
                    pc = K.poses(p['c2w'], len(p['ids']))[p['slots']]
                    row['compare'][mine+'_vs_prior'] = dict(pair(cams[mine], pc), prior_rr_deg=K.relative(pc, gt)['rotation_deg']['rms'])
    count = sum(a.get('raw_match_count', 0) for r in data['rows'] for a in r['arms'])
    total = sum(len(a.get('raw_sha256', [])) for r in data['rows'] for a in r['arms'])
    if data.get('raw_match_count') != count or data.get('raw_frame_count') != total:
        raise ValueError('Decode totals differ')
    main = verdict(rows, 'A', ('Bm', 'Cm'), data['stub'])
    continuity = verdict(rows, "A'", ("B'", "C'"), data['stub'])
    return dict(schema='k4-score-v1', rows=rows, verdict=main['verdict'], decision=main, continuity=continuity,
                rules=dict(baseline='A', arms=['Bm', 'Cm'], floor='max(|rr(A)-rr(A2)|, |rr(A)-rr(A\')|)',
                           repaired='similarity class gross at A, not gross at arm, rr drop > floor',
                           confirm='>=3/5 failing captures repaired at Bm or Cm, no reference rise > 2 deg + floor at Bm or Cm',
                           refute='<=1/5 repaired at Bm and <=1/5 repaired at Cm', otherwise='inconclusive',
                           complete='every arm returned for every capture'),
                interpretation='GT conclusions remain conditional on REPORT9 binding. Metric scale and gravity are frozen T1 values. '
                               'Similarity fits determine class; rigid fits retain the round-5 rule.')


def cpu_summary(data, reference):
    if data.get('mode') != 'cpu':
        raise ValueError('Not a CPU check return')
    arm = data['rows'][0]['arms'][0]
    out = dict(complete=data['complete'], error=data.get('error'), error_detail=data.get('error_detail'),
               unit_status=arm['status'], load_seconds=data.get('load_seconds'), decode_all_seconds=data.get('decode_all_seconds'),
               staging_seconds=data.get('staging_seconds'), total_seconds=data.get('total_seconds'), exit_code=data.get('exit_code'))
    if arm['status'] == 'ok':
        plan = reference['captures'][0]['arms'][0]
        c = np.asarray(arm['c2w'], float)
        out.update(unit_seconds=arm['seconds'], unit_inference_seconds=arm['inference_seconds'], rss_kib=arm['rss_kib'],
                   finite=bool(np.isfinite(c).all()), shape=list(c.shape), ids_match=arm['ids'] == plan['ids'],
                   unit_rr_vs_gt_deg=K.relative(c[plan['slots']], K.poses(reference['captures'][0]['gt']))['rotation_deg']['rms'],
                   unit_vs_t1_deg=K.relative(c[plan['slots']], K.poses(reference['captures'][0]['t1']))['rotation_deg']['rms'])
    per, frames, matches = {}, 0, 0
    for row, ref in zip(data.get('decoded', []), reference['captures']):
        if row['key'] != ref['key']:
            raise ValueError('Capture order differs')
        for label, a, plan in zip(LABELS, row['arms'], ref['arms']):
            if a is None or a['frames'] != len(plan['ids']) or len(a['raw_sha256']) != a['frames']:
                raise ValueError('Decode record differs')
            check_versions(a['decode_versions'])
            m = sum(h == e for h, e in zip(a['raw_sha256'], plan['raw_sha256']))
            if m != a['raw_match_count']:
                raise ValueError('Decode match count differs')
            per.setdefault(label, [0, 0])
            per[label][0] += m
            per[label][1] += a['frames']
            frames += a['frames']
            matches += m
    out.update(decoded_frames=frames, decoded_matches=matches, per_arm_matches=per,
               versions=data['decoded'][0]['arms'][0]['decode_versions'] if data.get('decoded') else None)
    return out


def render(result):
    f = lambda x: 'undefined' if x is None else f'{x:.4f}'
    d, c = result['decision'], result['continuity']
    lines = [f"Coverage verdict (Bm, Cm vs A): **{d['verdict']}**; continuity (B', C' vs A'): **{c['verdict']}**.",
             result['interpretation'], '']
    for name, v in (('Coverage', d), ('Continuity', c)):
        if 'repaired' in v:
            lines.append(f"{name}: gross at {v['baseline']} {v['gross_at_baseline']}/5; repaired "
                         + '; '.join(f"{x} {len(v['repaired'][x])}/5" for x in v['arms'])
                         + f"; any {len(v['repaired_any'])}/5; reference violations {len(v['reference_violations'])}.")
        else:
            lines.append(f"{name}: {v['reason']}.")
    lines += ['', '| Capture | Arm | Rigid | Similarity | Rel rot RMS ° | Rigid trans RMS m | Sim trans RMS m | Sim scale | Scale/A | Gravity mean/max ° | Raw match |',
              '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for row in result['rows']:
        for label, a in row['arms'].items():
            if a['status'] != 'ok':
                lines.append('| '+' | '.join([row['capture'], label, a['status']]+['—']*8)+' |')
                continue
            r, s, g = a['rigid'], a['similarity'], a['gravity']
            lines.append('| '+' | '.join([row['capture'], label, r['classification'], s['classification'],
                f(a['relative']['rotation_deg']['rms']), f(r['translation_rms_m']), f(s['translation_rms_m']), f(s['scale']),
                f(s.get('scale_relative_to_A')), f(g['mean_deg'])+' / '+f(g['max_deg']), f"{a['raw_match_count']}/{a['frames']}"])+' |')
    lines += ['', '| Capture | A–T1 rot ° / ctr m | A–A2 rot ° / ctr m | A–A\' rot ° / ctr m | Floor ° |', '| --- | --- | --- | --- | --- |']
    for row in result['rows']:
        cells = []
        for k in ('A_vs_T1', 'A_vs_A2', "A_vs_A'"):
            v = row['compare'].get(k)
            cells.append(f(v['relative_rotation_rms_deg'])+' / '+f(v['center_rms_m']) if v else 'missing')
        lines.append('| '+' | '.join([row['capture']]+cells+[f(row['floor_deg'])])+' |')
    if any("A'_vs_prior" in r['compare'] for r in result['rows']):
        lines += ['', "| Capture | A' vs prior A' rot ° / ctr m | B' vs prior B rot ° / ctr m |", '| --- | --- | --- |']
        for row in result['rows']:
            cells = [f(v['relative_rotation_rms_deg'])+' / '+f(v['center_rms_m']) if (v := row['compare'].get(k)) else 'missing'
                     for k in ("A'_vs_prior", "B'_vs_prior")]
            lines.append('| '+' | '.join([row['capture']]+cells)+' |')
    return '\n'.join(lines)+'\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--return', dest='returned', type=Path)
    ap.add_argument('--receipt', type=Path)
    ap.add_argument('--reference', type=Path, default=Path(__file__).with_name('REFERENCE_K4.json'))
    ap.add_argument('--prior', type=Path, help='173701 5.json for the continuity comparison')
    ap.add_argument('--cpu', type=Path, help='CPU check 4.1.json: print its summary and stop')
    ap.add_argument('--out', type=Path, default=Path(__file__).parent/'scored')
    a = ap.parse_args()
    ref = json.loads(a.reference.read_text())
    if a.cpu:
        print(json.dumps(cpu_summary(json.loads(a.cpu.read_text()), ref), indent=1))
        return
    data, receipt = [json.loads(p.read_text()) for p in (a.returned, a.receipt)]
    if (a.returned.stat().st_size >= 3_200_000 or receipt['sha256'] != sha(a.returned)
            or receipt['bytes'] != a.returned.stat().st_size or data['token'] != ref['token']
            or receipt['token'] != ref['token'] or receipt['complete'] != data['complete']
            or receipt['stub'] != data['stub'] or receipt['input_sha256'] != ref['input_sha256']):
        raise ValueError('Return receipt differs')
    prior = json.loads(a.prior.read_text()) if a.prior else None
    result = score(data, ref, prior)
    result['provenance'] = dict(return_sha256=sha(a.returned), receipt_sha256=sha(a.receipt), reference_sha256=sha(a.reference),
                                prior_sha256=sha(a.prior) if a.prior else None)
    a.out.mkdir(exist_ok=True, parents=True)
    for name, raw in [('K4.json', json.dumps(result, indent=2, allow_nan=False)+'\n'), ('K4.md', render(result))]:
        with (a.out/name).open('x') as f:
            f.write(raw)
    print(result['verdict'])


if __name__ == '__main__':
    main()
