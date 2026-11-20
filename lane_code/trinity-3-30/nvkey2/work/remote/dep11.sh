K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
$P -B - <<'PY'
import json, os
src = [json.loads(l) for l in open('queue/45_v6p30.jsonl')]
for job, model, eff, tag in (('47_v6p30argmed', 'gcp/google/gemini-4-argon', 'medium', 'gemini-4-argon-medium'), ('48_v6p30astra', 'openai/openai/gpt-6.2-astra', 'high', 'gpt-6.2-astra')):
    out = []
    for t in src:
        t2 = json.loads(json.dumps(t)); t2['model'] = model; t2['effort'] = eff; t2['id'] = t['id'].rsplit('_', 1)[0] + '_' + tag
        t2['meta']['variant'] = '%s %s' % (model, eff); out.append(t2)
    open('queue/.%s.tmp' % job, 'w').write(''.join(json.dumps(t) + '\n' for t in out)); os.replace('queue/.%s.tmp' % job, 'queue/%s.jsonl' % job); print(job, len(out))
PY
sleep 6; tail -3 runner.log
