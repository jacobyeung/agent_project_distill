#!/bin/bash
set -u
O=/scratch/jjyeung/n30_mirror/dist_diag/coverage_v1
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY' 1>&2
import json, gzip, re, hashlib
O='/scratch/jjyeung/n30_mirror/dist_diag/coverage_v1/'
want=set()
for n in ('COVERAGE_UNITS_V1.jsonl','COVERAGE_DISTANCE_V1.jsonl'):
    for l in open(O+n):
        want.add(re.sub(r'_dd\d\d$','',json.loads(l)['qid']))
src=['/scratch/jjyeung/n30_mirror/rows_r1/out/vehN_units/repaired/rows_slice.jsonl','/scratch/jjyeung/n30_mirror/rows_r2/out/vehN_pool_abs_distance_full/repaired/rows.jsonl']
rows=[]
for p in src:
    for l in open(p):
        if l.strip() and json.loads(l)['qid'] in want: rows.append(l if l.endswith('\n') else l+'\n')
blob=''.join(rows).encode()
with gzip.GzipFile(O+'COVERAGE_SOURCES_V1.jsonl.gz','wb',mtime=0) as f: f.write(blob)
print('sources', len(rows), 'of', len(want), 'raw sha', hashlib.sha256(blob).hexdigest())
PY
sha256sum $O/COVERAGE_SOURCES_V1.jsonl.gz 1>&2
cat $O/COVERAGE_SOURCES_V1.jsonl.gz
