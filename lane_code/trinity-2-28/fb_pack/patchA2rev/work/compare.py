"""Compare harness results between trees; write COMPARE.json."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

W = Path(__file__).resolve().parent
R = {}
for label in ('base', 'a', 'a2', 'live_base', 'live_a2', 'a2_camform'):
    R[label] = json.loads((W/'results'/(label+'.json')).read_text())
KEYS = ('ok', 'exc', 'args', 'str', 'frames', 'cause', 'events', 'written', 'written_files', 'receipt.json', 'membership.json')

LEGACY = ('SN|', 'VB|', 'MEM|', 'CN|', 'CD|', 'RE|legacy', 'RV|legacy', 'RE|original')
DECLARED = ('DS|', 'DV|', 'DB|', 'DM|', 'DC|', 'RE|declared', 'RV|declared')


def view(rec):
    return {k: rec.get(k) for k in KEYS}


def outcome(rec):
    if 'ok' in rec:
        return 'OK' + (' wrote ' + ','.join(rec['written_files']) if rec.get('written_files') else '')
    return rec['exc'] + ': ' + rec['str'][:160]


def diff(x, y, prefixes):
    a, b = R[x]['results'], R[y]['results']
    names = sorted(k for k in set(a) | set(b) if k.startswith(prefixes))
    out, fields = [], Counter()
    for k in names:
        if k not in a or k not in b:
            out.append(dict(case=k, missing_in=x if k not in a else y))
            continue
        va, vb = view(a[k]), view(b[k])
        if va != vb:
            changed = [f for f in KEYS if va.get(f) != vb.get(f)]
            fields.update(changed)
            out.append(dict(case=k, fields=changed, **{x: outcome(a[k]), y: outcome(b[k])},
                            lines={x: a[k].get('lines'), y: b[k].get('lines')}))
    return dict(compared=len(names), differing=len(out), fields=dict(fields), cases=out)


def count(label, prefixes):
    return sum(1 for k in R[label]['results'] if k.startswith(prefixes))


result = dict(inputs_sha256={str(W/'results'/(l+'.json')): hashlib.sha256((W/'results'/(l+'.json')).read_bytes()).hexdigest() for l in R},
              meta={l: R[l]['meta'] for l in R},
              counts={l: {p: count(l, (p,)) for p in LEGACY + DECLARED} for l in R})
result['legacy_base_vs_a2'] = diff('base', 'a2', LEGACY)
result['legacy_base_vs_a'] = diff('base', 'a', LEGACY)
result['legacy_live_base_vs_live_a2'] = diff('live_base', 'live_a2', LEGACY)
result['declared_a_vs_a2'] = diff('a', 'a2', DECLARED)
result['all_a2_vs_live_a2'] = diff('a2', 'live_a2', LEGACY + DECLARED)
result['all_base_vs_live_base'] = diff('base', 'live_base', LEGACY + DECLARED)
result['all_a2_vs_a2_camform'] = diff('a2', 'a2_camform', LEGACY + DECLARED)
(W/'COMPARE.json').write_text(json.dumps(result, indent=1)+'\n')
for k, v in result.items():
    if isinstance(v, dict) and 'compared' in v:
        print(k, 'compared', v['compared'], 'differing', v['differing'], v['fields'])
        for c in v['cases'][:int(sys.argv[1]) if len(sys.argv) > 1 else 40]:
            print('   ', c['case'][:70].ljust(70), '|', *(c.get(l, '')[:90] for l in k.split('_vs_')[0].split('_', 1)[-1:]),
                  '||', c.get(k.split('_vs_')[1], c.get('missing_in', ''))[:90] if isinstance(c.get(k.split('_vs_')[1], ''), str) else '')
