"""Local CPU scorer for the K5 arms (rules fixed in REPORT_K5.md before any run)."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics

import numpy as np

ARM_NAMES = ['A1', 'A2', 'D1', 'D2']
TOWER = ('p9', 'd', 'dc', 'pt')
ALL = TOWER+('K', 'cm', 'cu', 's')
DATASETS = ('ScanNet', 'ScanNet++', 'ARKit')


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def authenticated(directory, group):
    """Return the group result only if its receipt matches its bytes."""
    d = Path(directory)
    raw = (d/('5%d.json' % group)).read_bytes()
    receipt = json.loads((d/('5%d.1.json' % group)).read_text())
    if receipt['sha256'] != hashlib.sha256(raw).hexdigest() or receipt['bytes'] != len(raw) or receipt['group'] != group:
        raise ValueError('receipt does not authenticate result %d' % group)
    state = d/('12%d.txt' % group)
    if state.is_file() and state.read_text().split()[0] != receipt['job']:
        raise ValueError('receipt job differs from fetched job %d' % group)
    return json.loads(raw)


def arms_from(results):
    arms = {}
    for result in results:
        for a in result['arms']:
            if a['arm'] in arms:
                raise ValueError('arm returned twice')
            arms[a['arm']] = a
    return arms


def split_records(arm, n):
    """First record per capture key, plus the final capture-0 recompute."""
    first, recompute = {}, None
    for r in arm.get('records', []):
        if r.get('status') != 'ok':
            continue
        if r['position'] == n and r['index'] == 0:
            recompute = r
        elif r['k'] not in first:
            first[r['k']] = r
    return first, recompute


def rot_deg(a, b):
    a, b = np.asarray(a, float)[:, :3, :3], np.asarray(b, float)[:, :3, :3]
    rel = np.einsum('nji,njk->nik', a, b)
    cos = np.clip((np.trace(rel, axis1=1, axis2=2)-1)/2, -1, 1)
    return float(np.degrees(np.arccos(cos)).max())


def trans_m(a, b):
    a, b = np.asarray(a, float)[:, :3, 3], np.asarray(b, float)[:, :3, 3]
    return float(np.linalg.norm(a-b, axis=1).max())


def compare(a, b):
    """Bit equality and maximum deviations between two capture records."""
    names = [n for n in ALL if n in a['sha'] and n in b['sha']]
    value = dict(bit=all(a['sha'][n] == b['sha'][n] for n in names),
                 tower_bit=all(a['sha'][n] == b['sha'][n] for n in TOWER),
                 translation_m=trans_m(a['cm'], b['cm']), translation_unscaled=trans_m(a['cu'], b['cu']),
                 rotation_deg=rot_deg(a['cm'], b['cm']),
                 K=float(np.abs(np.asarray(a['K'], float)-np.asarray(b['K'], float)).max()),
                 scale=abs(a['s']-b['s']), scale_rel=abs(a['s']-b['s'])/abs(b['s']))
    return value


def summarize(rows, keys, ref):
    out = {}
    for ds in DATASETS+('all',):
        want = [k for k in keys if ds == 'all' or ref[k]['dataset'] == ds]
        have = [rows[k] for k in want if k in rows]
        entry = dict(captures=len(want), compared=len(have), missing=len(want)-len(have))
        if have:
            entry['bit_equal'] = sum(r['bit'] for r in have)
            entry['tower_bit_equal'] = sum(r['tower_bit'] for r in have)
            for f in ('translation_m', 'translation_unscaled', 'rotation_deg', 'K', 'scale', 'scale_rel'):
                vals = [r[f] for r in have]
                entry[f] = dict(max=max(vals), median=statistics.median(vals))
        out[ds] = entry
    return out


def pair(arms, x, y, keys, n, ref):
    if x not in arms or y not in arms:
        return dict(status='missing arm')
    fx, _ = split_records(arms[x], n)
    fy, _ = split_records(arms[y], n)
    rows = {k: compare(fx[k], fy[k]) for k in keys if k in fx and k in fy}
    return dict(status='complete' if len(rows) == len(keys) else 'incomplete',
                summary=summarize(rows, keys, ref), per_capture=rows)


def recompute(arms, a, keys, n):
    if a not in arms:
        return dict(status='missing arm')
    first, again = split_records(arms[a], n)
    k0 = keys[0]
    if again is None or k0 not in first:
        return dict(status='incomplete')
    return dict(status='complete', **compare(again, first[k0]))


def versus_dump(arms, keys, n, ref):
    if 0 not in arms:
        return dict(status='missing arm')
    first, _ = split_records(arms[0], n)
    rows = {}
    for k in keys:
        d = ref[k].get('dump')
        if not d or k not in first:
            continue
        r = first[k]
        cu = np.asarray(r['cu'], float)
        fixed = cu.copy()
        fixed[:, :3, 3] *= d['scale']
        rows[k] = dict(K_bit=r['K'] == d['K'], K=float(np.abs(np.asarray(r['K'])-np.asarray(d['K'])).max()),
                       unscaled_bit=r['cu'] == d['c2w_unscaled'],
                       unscaled_translation=trans_m(r['cu'], d['c2w_unscaled']),
                       unscaled_rotation_deg=rot_deg(r['cu'], d['c2w_unscaled']),
                       metric_fixed_bit=fixed.tolist() == d['c2w_metric'],
                       metric_fixed_translation_m=trans_m(fixed, d['c2w_metric']),
                       served_plane_bit=r['sha'].get('df', {}).get('sha256') == d['depth_sha256'],
                       scale_vs_served_rel=abs(r['s']-d['scale'])/d['scale'])
    want = [k for k in keys if ref[k].get('dump')]
    out = {}
    for ds in DATASETS+('all',):
        sel = [rows[k] for k in want if k in rows and (ds == 'all' or ref[k]['dataset'] == ds)]
        if not sel:
            out[ds] = dict(compared=0)
            continue
        out[ds] = dict(compared=len(sel), K_bit=sum(x['K_bit'] for x in sel),
                       served_plane_bit=sum(x['served_plane_bit'] for x in sel),
                       unscaled_bit=sum(x['unscaled_bit'] for x in sel),
                       metric_fixed_bit=sum(x['metric_fixed_bit'] for x in sel),
                       max_K=max(x['K'] for x in sel),
                       max_unscaled_translation=max(x['unscaled_translation'] for x in sel),
                       max_unscaled_rotation_deg=max(x['unscaled_rotation_deg'] for x in sel),
                       max_metric_fixed_translation_m=max(x['metric_fixed_translation_m'] for x in sel),
                       max_scale_vs_served_rel=max(x['scale_vs_served_rel'] for x in sel))
    return dict(status='complete' if len(rows) == len(want) else 'incomplete', summary=out, per_capture=rows)


def stats(vals):
    return dict(n=len(vals), mean=statistics.fmean(vals), median=statistics.median(vals), max=max(vals)) if vals else dict(n=0)


def cost(arms, keys, n, ref):
    """Tower seconds per capture, D against A on the same captures, excluding rebuild calls."""
    out = {}
    pairs = [(0, 2), (1, 3)]
    for ds in DATASETS+('all',):
        a_vals, d_vals = [], []
        for ia, idd in pairs:
            if ia not in arms or idd not in arms:
                continue
            fa, _ = split_records(arms[ia], n)
            fd, _ = split_records(arms[idd], n)
            for k in keys:
                if (ds != 'all' and ref[k]['dataset'] != ds) or k not in fa or k not in fd:
                    continue
                if fa[k]['rebuilt'] or fd[k]['rebuilt']:
                    continue
                a_vals.append(fa[k]['seconds'])
                d_vals.append(fd[k]['seconds'])
        entry = dict(A=stats(a_vals), D=stats(d_vals))
        if a_vals:
            entry['ratio_of_means'] = statistics.fmean(d_vals)/statistics.fmean(a_vals)
            entry['ratio_of_medians'] = statistics.median(d_vals)/statistics.median(a_vals)
        out[ds] = entry
    out['arm_wall_seconds'] = {ARM_NAMES[a]: arms[a].get('wall_seconds') for a in sorted(arms)}
    out['rebuild_seconds'] = {ARM_NAMES[a]: [r['seconds'] for r in arms[a].get('records', []) if r.get('rebuilt')]
                              for a in sorted(arms)}
    out['peak_bytes'] = {ARM_NAMES[a]: max([r.get('peak_bytes', 0) for r in arms[a].get('records', [])] or [0])
                         for a in sorted(arms)}
    return out


def answers(result, arms, keys):
    d = result['D1_vs_D2']
    q1 = 'incomplete'
    complete = (d.get('status') == 'complete' and all(result['recompute'][x].get('status') == 'complete'
                                                       for x in ('D1', 'D2')))
    if complete:
        ok = (d['summary']['all']['bit_equal'] == len(keys)
              and all(result['recompute'][x]['bit'] for x in ('D1', 'D2')))
        q1 = 'yes' if ok else 'no'
    a = result['A1_vs_A2']
    baseline = 'incomplete'
    if a.get('status') == 'complete':
        baseline = 'orders agree' if a['summary']['all']['bit_equal'] == len(keys) else 'orders differ'
    c = result['cost']['all']
    warn = {ARM_NAMES[x]: arms[x].get('warn_only') for x in sorted(arms) if x in (2, 3)}
    return dict(q1_deterministic_orders_bit_equal=q1, default_orders=baseline,
                q2_cost_ratio_of_means=c.get('ratio_of_means'), q2_cost_ratio_of_medians=c.get('ratio_of_medians'),
                deterministic_warn_only=warn,
                strict_refusals={ARM_NAMES[x]: [bytes.fromhex(o).decode() for o in arms[x].get('strict_attempt', {}).get('ops', [])]
                                 for x in sorted(arms) if 'strict_attempt' in arms[x]})


def score(results, ref_path):
    ref_all = json.loads(Path(ref_path).read_text())
    ref = {c['k']: c for c in ref_all['captures']}
    keys = [c['k'] for c in sorted(ref_all['captures'], key=lambda c: c['position'])]
    n = len(keys)
    arms = arms_from(results)
    result = dict(arms_present=[ARM_NAMES[a] for a in sorted(arms)],
                  arm_status={ARM_NAMES[a]: arms[a].get('status') for a in sorted(arms)})
    result['A1_vs_A2'] = pair(arms, 0, 1, keys, n, ref)
    result['D1_vs_D2'] = pair(arms, 2, 3, keys, n, ref)
    result['A1_vs_D1'] = pair(arms, 0, 2, keys, n, ref)
    result['A2_vs_D2'] = pair(arms, 1, 3, keys, n, ref)
    result['recompute'] = {ARM_NAMES[a]: recompute(arms, a, keys, n) for a in range(4)}
    result['A1_vs_rank1'] = versus_dump(arms, keys, n, ref)
    result['cost'] = cost(arms, keys, n, ref)
    result['answers'] = answers(result, arms, keys)
    return result


def markdown(result):
    lines = ['# K5 score', '', '## Answers', '```', json.dumps(result['answers'], indent=1), '```', '']
    for name in ('A1_vs_A2', 'D1_vs_D2', 'A1_vs_D1', 'A2_vs_D2'):
        r = result[name]
        lines.append('## '+name+' ('+r['status']+')')
        if 'summary' in r:
            lines.append('| dataset | compared | bit-equal | tower bit-equal | max t m | max rot deg | max K | max scale rel |')
            lines.append('| --- | --- | --- | --- | --- | --- | --- | --- |')
            for ds, e in r['summary'].items():
                if e.get('compared'):
                    lines.append('| %s | %d/%d | %d | %d | %.3g | %.3g | %.3g | %.3g |' % (
                        ds, e['compared'], e['captures'], e['bit_equal'], e['tower_bit_equal'],
                        e['translation_m']['max'], e['rotation_deg']['max'], e['K']['max'], e['scale_rel']['max']))
        lines.append('')
    lines += ['## Capture-0 recompute', '```', json.dumps(result['recompute'], indent=1), '```',
              '## A1 vs rank 1 dump', '```', json.dumps(result['A1_vs_rank1'].get('summary'), indent=1), '```',
              '## Cost', '```', json.dumps(result['cost'], indent=1), '```']
    return '\n'.join(lines)+'\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--returned', nargs='+', required=True, help='directories holding 5<g>.json and 5<g>.1.json')
    ap.add_argument('--reference', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    results = []
    for d in a.returned:
        g = int(next(Path(d).glob('5?.1.json')).name[1])
        results.append(authenticated(d, g))
    value = score(results, a.reference)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    (out/'SCORE_K5.json').write_text(json.dumps(value, indent=1, allow_nan=False)+'\n')
    (out/'SCORE_K5.md').write_text(markdown(value))
    print(json.dumps(value['answers'], indent=1))


if __name__ == '__main__':
    main()
