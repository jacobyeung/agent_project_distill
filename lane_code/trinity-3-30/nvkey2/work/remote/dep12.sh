K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%T; cat meter/METER.json; wc -l out/4*.jsonl; tail -2 runner.log
cd kit && $P -B v2_jobs.py $K/queue/.56.tmp gcp/google/gemini-4-argon high 30 o4 && $P -B v2_jobs.py $K/queue/.56.tmp openai/openai/gpt-6.2-astra high 30 o4 && cd $K && $P -B - <<'PY'
import json, os
ts = [json.loads(l) for l in open('queue/.56.tmp')]
for t in ts: t['meta']['note'] = 'uncertified namer; candidates only; V2 failed its control bar (55_v2cal: Argon top-3 81.1 [75.1, 86.8], top-5 87.4; Opus 71.4); binds only via the consumer spec PHRASE certification and fold rule'
open('queue/.56b.tmp', 'w').write(''.join(json.dumps(t) + '\n' for t in ts)); os.replace('queue/.56b.tmp', 'queue/56_v2o4.jsonl'); os.rename('queue/.56.tmp', 'v2/.56_build.unused')
print('56_v2o4 tasks', len(ts), set(t['meta']['tag'] for t in ts), len(set(i for t in ts for i in t['meta']['items'])))
PY
sleep 6; tail -2 runner.log
