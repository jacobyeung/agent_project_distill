import json, hashlib, base64
from pathlib import Path
L = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24v')
def cap(p):
    v = json.loads(Path(p).read_text())
    if isinstance(v, dict) and v.get('encoding') == 'base64-json':
        return json.loads(base64.b64decode(v['payload']))
    return v
def diff(a, b, path=''):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a: out.append(f'+ {path}.{k} = {json.dumps(b[k])[:160]}')
            elif k not in b: out.append(f'- {path}.{k} = {json.dumps(a[k])[:160]}')
            else: out += diff(a[k], b[k], f'{path}.{k}')
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)): out += diff(x, y, f'{path}[{i}]')
    elif a != b:
        out.append(f'~ {path}: {json.dumps(a)[:120]} -> {json.dumps(b)[:120]}')
    return out
for kit, rel in [('n_go', 'out/kit_n_go'), ('qd', 'out/kit_qd'), ('n', 'work/build24/kits/n'), ('q', 'work/build24/kits/q')]:
    for f in ('c.json', 'n.json', 'a.json', 'p.json', '7.json', 'c0.json'):
        old = L/'attic/build24m4v'/rel/'k'/f; new = L/rel/'k'/f
        if not old.exists(): print(kit, f, 'NO ORIGINAL'); continue
        d = diff(cap(old), cap(new))
        print(f'== {kit} {f}: {len(d)} diffs')
        for line in d[:25]: print('  ', line)
