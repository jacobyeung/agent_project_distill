#!/usr/bin/env python3
"""Build the staging file list (carry + tower union) for trinity-2-28; run on trinity-1-18."""
import json, os, csv, collections, sys
R = '/scratch/jjyeung/orch_n30'
OUT = R + '/sb_stage228'
os.makedirs(OUT, exist_ok=True)
roots = []
st = json.load(open(R + '/sb_cachk/out/v2/STAGING.json'))
for it in st['items']:
    ps = it['path'] if isinstance(it['path'], list) else [it['path']]
    if 'dense frames' in it['kind']:
        continue
    roots += ps
frames = [l.strip() for l in open(R + '/sb_cachk/out/v2/STAGING_FRAMES.txt') if l.strip()]
kinds = collections.Counter()
tower = []
with open(R + '/sb_ktfix2/out/STAGE_LIST.tsv') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        kinds[row['kind']] += 1
        if row['kind'] != 'create':
            tower.append(row['path'])
print('tower kinds', dict(kinds), file=sys.stderr)
entries = set()
missing = []
def add(p):
    if os.path.islink(p) or os.path.isfile(p):
        entries.add(p)
    elif os.path.isdir(p):
        entries.add(p)
        for d, dn, fn in os.walk(p):
            for n in dn:
                entries.add(os.path.join(d, n))
            for n in fn:
                entries.add(os.path.join(d, n))
    else:
        missing.append(p)
for p in roots + frames + tower:
    add(p)
nbytes = sum(os.lstat(p).st_size for p in entries if not os.path.isdir(p) or os.path.islink(p))
nfiles = sum(1 for p in entries if os.path.isfile(p) and not os.path.islink(p))
lst = sorted(entries)
open(OUT + '/union.list', 'w').write('\n'.join(lst) + '\n')
json.dump(dict(entries=len(lst), files=nfiles, bytes=nbytes, missing=missing, carry_roots=len(roots), frames=len(frames), tower_paths=len(tower)), open(OUT + '/union_stats.json', 'w'), indent=1)
print(json.dumps(dict(entries=len(lst), files=nfiles, GB=round(nbytes / 1e9, 3), missing=missing[:10], n_missing=len(missing))))
