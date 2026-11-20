"""nv_orch1 (copy of nvkey1 ledger.py, reading the pulled Orchard meter work/opull/meter/CALLS.jsonl): append one line per (job, model) to distill_design/NV_SPEND_LEDGER.jsonl from the runner's meter, for jobs given on the command line
(only when that job has no line yet for that model). usage: ledger.py PURPOSE_JSON  where PURPOSE_JSON = {"job": "purpose", ...}"""
import json, sys, collections, os, time
K = '/scratch/jjyeung/orch_n30/nv_orch1/work/opull'; LED = '/data2/jjyeung/agent_project_data/distill_design/NV_SPEND_LEDGER.jsonl'
purpose = json.loads(sys.argv[1]); seen = set()
if os.path.exists(LED):
    for l in open(LED):
        try: d = json.loads(l); seen.add((d.get('job'), d.get('model'), d.get('lane')))
        except Exception: pass
agg = collections.defaultdict(lambda: collections.Counter())
for l in open(K + '/meter/CALLS.jsonl'):
    r = json.loads(l)
    if r['job'] not in purpose: continue
    c = agg[(r['job'], r['model'])]; c['calls'] += 1; c['ok'] += r['status'] == 200; c['faults'] += bool(r.get('fault'))
    c['input_tokens'] += r.get('prompt_tokens') or 0; c['output_tokens'] += r.get('completion_tokens') or 0; c['thinking_tokens'] += r.get('reasoning_tokens') or 0
    c['dollars_list'] += r.get('dollars') or 0.0; c['dollars_proxy'] += float(r.get('header_cost') or 0); c['bytes'] += r.get('bytes') or 0
    c['first'] = c['first'] or r['utc']; c['last'] = r['utc']
with open(LED, 'a') as f:
    for (job, model), c in sorted(agg.items()):
        if (job, model, 'nv_orch1') in seen: continue
        f.write(json.dumps(dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), lane='nv_orch1', host='orchard-preempt', job=job, model=model, calls=c['calls'], ok=c['ok'], faults=c['faults'],
                                input_tokens=c['input_tokens'], output_tokens=c['output_tokens'], thinking_tokens_in_output=c['thinking_tokens'],
                                dollars_list=round(c['dollars_list'], 4), dollars_proxy_reported=round(c['dollars_proxy'], 4), request_bytes=c['bytes'],
                                first=c['first'], last=c['last'], purpose=purpose[job],
                                note='list = catalogue price x tokens (thinking billed as output); proxy = x-litellm-response-cost after the proxy discount; the NV charge-back rate is not visible')) + '\n')
        print('ledger', job, model, c['calls'], round(c['dollars_list'], 3))
