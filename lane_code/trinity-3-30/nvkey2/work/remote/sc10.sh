K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%T; wc -l out/4*.jsonl out/56*.jsonl; tail -2 runner.log; tail -1 v6/chain.log; cat faults/*.gaveup.jsonl | tail -5
$P -B - <<'PY'
import json, collections, statistics
st = collections.defaultdict(list); c = collections.Counter()
for l in open('meter/CALLS.jsonl'):
    r = json.loads(l)
    if r['job'] in ('45_v6p30', '46_v6v30', '47_v6p30argmed', '48_v6p30astra'):
        c[(r['job'], r['status'])] += 1
        if r['status'] == 200: st[r['job']].append(r['secs'])
print(dict(c))
for j, v in sorted(st.items()): print(j, len(v), 'median', statistics.median(v), 'max', max(v), '>300s', sum(x > 300 for x in v))
PY
V6_TAG=V6_argmed_vs_astra timeout 300 $P -B kit/score_v6.py out/47_v6p30argmed.jsonl out/48_v6p30astra.jsonl > scores/V6_argmed_vs_astra.txt 2>&1; echo rc $?; $P -B -c "
import json; d=json.load(open('scores/V6_argmed_vs_astra.json'))
for k in ('parsed','primary_named','verifier_named','two_family_named','check_nouns','blind_inventory','O3_gate'): print(k, json.dumps(d.get(k)))"
