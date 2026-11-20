K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
$P -B - <<'PY'
import json, gzip, os, collections, glob, sys
sys.path.insert(0, 'kit'); import excl
cat = collections.Counter(); pr = collections.Counter(); names = collections.Counter(); rowsn = collections.Counter(); per = collections.defaultdict(set); folds = collections.defaultdict(set)
ex = collections.Counter(); splits = collections.Counter()
for f in sorted(glob.glob('v2/noprop/caps/*.json.gz')):
    d = json.load(gzip.open(f)); splits[d.get('k1_split')] += 1
    r = excl.reasons(d['capture']); ex[tuple(r)] += 1
    for row in d['rows']:
        for o in row['operands']: rowsn[o] += 1
    for nm, v in d['names'].items():
        k0 = (v.get('keys') or {}).get('k0') or {}
        c = k0.get('category'); cat[c] += 1; pr[(c, k0.get('pool_recall'))] += 1
        if c != 'good': per[nm].add((d['capture'], v.get('instance'))); folds[nm].add(d.get('fold'))
print('captures', len(glob.glob('v2/noprop/caps/*.json.gz')), dict(splits), 'excl', dict(ex))
print('categories', dict(cat)); print('cat x pool_recall', dict(pr))
top = sorted(per, key=lambda n: -rowsn[n])
print('non-good names', len(per), [(n, rowsn[n], len(per[n]), len(folds[n])) for n in top[:25]])
print('names with >=5 inst over >=3 folds', sum(1 for n in per if len(per[n]) >= 5 and len(folds[n]) >= 3), sum(len(per[n]) for n in per if len(per[n]) >= 5 and len(folds[n]) >= 3))
PY
