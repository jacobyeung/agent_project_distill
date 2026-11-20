import json, gzip, re, collections
from pathlib import Path
D = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24v/work/build24m4v')
rd = json.loads(gzip.decompress((D/'published/rd0/rdiff.json.gz').read_bytes()))
print('top keys', list(rd.keys()))
for k, v in rd.items():
    if isinstance(v, list): print(k, len(v), 'example', json.dumps(v[0])[:300])
    else: print(k, json.dumps(v)[:300])
names = set(json.loads((D/'SOURCES.json').read_text())['names'])
def pat(q):
    return re.sub(r'[0-9a-f]{6,}', 'H', re.sub(r'(?<=_)[0-9]+', 'N', q))
c = collections.Counter()
for x in rd['N']:
    k = x['key']; c[(k[3], k[3] in names, pat(k[2]), k[2].startswith('a0_'))] += 1
for key, n in sorted(c.items(), key=lambda t: -t[1])[:40]: print(n, key)
print('N fields', sorted(rd['N'][0].keys()))
receipt = json.loads((D/'c072905b.json').read_text())['rows']
ex = [x for x in rd['N'] if x['key'][3] in names and not x['key'][2].startswith('a0_')]
print('exemptible with receipt entry (same qid):', sum(x['key'][2] in receipt for x in ex), 'of', len(ex))
a0 = [x for x in rd['N'] if x['key'][2].startswith('a0_')]
print('a0 rows', len(a0), 'with entry', sum(x['key'][2] in receipt for x in a0), 'sources', collections.Counter(x['key'][3] for x in a0))
