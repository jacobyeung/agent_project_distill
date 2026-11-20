import sys, json, hashlib, base64, tarfile
from pathlib import Path
L = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24v')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cap(p):
    v = json.loads(Path(p).read_text())
    if isinstance(v, dict) and v.get('encoding') == 'base64-json':
        raw = base64.b64decode(v['payload']); assert hashlib.sha256(raw).hexdigest() == v['sha256'], p
        return json.loads(raw)
    return v
for k in [L/'out/kit_n_go', L/'out/kit_qd', L/'work/build24/kits/n', L/'work/build24/kits/q']:
    listed = {}
    for line in (k/'SHA256SUMS.txt').read_text().splitlines():
        h, n = line.split('  ', 1); listed[n] = h
    actual = {str(p.relative_to(k)): sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('BUILD.json', 'SHA256SUMS.txt')}
    b = cap(k/'BUILD.json')
    print(k.name, 'sums_match', listed == actual, 'missing', set(actual) ^ set(listed),
          'kit_sha', b.get('kit_sha256') == sha(k/'SHA256SUMS.txt'), 'cfg', b.get('config_sha256') == sha(k/'k/c.json'),
          'source_seal', b.get('source_seal'), 'GO', b.get('GO'))
    c = cap(k/'k/c.json'); n = cap(k/'k/n.json'); a = cap(k/'k/a.json'); s7 = cap(k/'k/7.json')
    print('  c.extent_receipt', json.dumps(c.get('extent_receipt'))[:200])
    print('  c.r1_training keys', sorted((c.get('r1_training') or {}).keys()))
    print('  c.pool_sources', (c.get('r1_training') or {}).get('extent_pool_sources'))
    print('  n.pool_sources', (n.get('r1_training') or {}).get('extent_pool_sources'), 'top', 'extent_pool_sources' in c, 'extent_pool_sources' in n)
    print('  n.extent_receipt', json.dumps(n.get('extent_receipt'))[:200])
    print('  a.GO', a.get('GO'), 'a.source', a.get('source'))
    print('  7.tree', s7.get('tree_sha256'), s7.get('archive'))
