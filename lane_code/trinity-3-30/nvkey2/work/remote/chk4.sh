K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%T; tail -6 runner.log; cat ctl/RATE ctl/INFLIGHT; ls faults
$P -B - <<'PY'
import json, collections
c = collections.Counter(); bad = []
for l in open('meter/CALLS.jsonl'):
    r = json.loads(l)
    if r['utc'] < '2026-11-20T04:45': continue
    c[(r['status'], r.get('waf', False))] += 1
    if r['status'] != 200: bad.append((r['utc'], r['job'], r['id'][:40], r['status'], r.get('secs'), (r.get('err') or '')[:160].replace('\n', ' ')))
print(dict(c))
for b in bad[-12:]: print(b)
PY
wc -l out/45_v6p30.jsonl out/46_v6v30.jsonl out/54_v1c_nearmiss.jsonl out/55_v2cal.jsonl
tail -3 /data3/jjyeung/orch_n13_20261026/nv_slots/ALLOC.md | cut -c1-200
