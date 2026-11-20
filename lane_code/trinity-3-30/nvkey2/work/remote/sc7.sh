K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%T; wc -l out/4*.jsonl out/5*.jsonl analysis_only/out/5*.jsonl 2>/dev/null | tail -9; tail -1 v6/chain.log; tail -2 runner.log
timeout 300 $P -B kit/score_v1.py c out/54_v1c_nearmiss.jsonl analysis_only/out/53_v1c_pilot.jsonl > scores/V1c.txt 2>&1; echo c rc $?; tr -d '\n' < scores/V1c.txt | cut -c1-4000; echo
timeout 300 $P -B kit/score_v1.py a out/50_v1a32.jsonl out/51_v1a64.jsonl > scores/V1a.txt 2>&1; echo a rc $?; $P -B -c "
import json; d=json.load(open('scores/V1a.json'))
for k,v in d.items():
    if k.startswith('agree'): print(k, json.dumps(v)); continue
    print(k, json.dumps({x: v[x] for x in ('calls_parsed','presence_>=1%','presence_absent','presence_decoy','presence_0.2-1%','point_>=1%','point_>=5%','point_1-5%','count_exact_truth1-4','first_frame_within1','decoy_count0') if x in v}))
"
