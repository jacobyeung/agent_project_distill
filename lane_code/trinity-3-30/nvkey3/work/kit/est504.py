"""nvkey3: count the proxy's 504 gateway timeouts (no usage in the reply) per (job, model) in K/meter/CALLS.jsonl and append one estimate line per
(job, model) to distill_design/NV_SPEND_LEDGER.jsonl (only when that pair has no estimate line yet and the job is complete).
Each 504 is priced at the mean list and proxy cost of the same job and model's completed calls (else the model's mean over all jobs): an upper bound
that assumes the upstream billed the whole call. usage: est504.py LANE [job,job,...|all] [--dry]"""
import json, sys, os, time, collections
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work'); LED = '/data2/jjyeung/agent_project_data/distill_design/NV_SPEND_LEDGER.jsonl'
LANE = sys.argv[1]; sel = sys.argv[2] if len(sys.argv) > 2 else 'all'; dry = '--dry' in sys.argv
have = set()
for l in open(LED):
    try: d = json.loads(l)
    except Exception: continue
    if d.get('kind') == 'gateway_504_estimate': have.add((d['job'], d['model']))
ok = collections.defaultdict(list); okm = collections.defaultdict(list); n504 = collections.Counter(); other = collections.Counter(); first = {}; last = {}
for l in open(K + '/meter/CALLS.jsonl'):
    r = json.loads(l); key = (r['job'], r['model'])
    if r.get('status') == 200 and (r.get('dollars') or 0) > 0:
        ok[key].append((r.get('dollars') or 0.0, float(r.get('header_cost') or 0))); okm[r['model']].append(ok[key][-1])
    elif r.get('status') == 504: n504[key] += 1; first.setdefault(key, r['utc']); last[key] = r['utc']
    elif not r.get('dollars'): other[(r['job'], r['model'], r.get('status'))] += 1
mean = lambda xs, i: sum(x[i] for x in xs) / len(xs) if xs else 0.0
tot = [0.0, 0.0]
for key in sorted(n504):
    job, model = key; base = ok.get(key) or okm.get(model) or []
    el, ep = n504[key] * mean(base, 0), n504[key] * mean(base, 1); tot[0] += el; tot[1] += ep
    print('504 %-22s %-34s n=%d est_list=%.3f est_proxy=%.3f basis=%s' % (job, model, n504[key], el, ep, 'job+model' if ok.get(key) else 'model'))
    if dry or key in have or not (sel == 'all' or job in sel.split(',')): continue
    with open(LED, 'a') as f:
        f.write(json.dumps(dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), lane=LANE, host=os.uname()[1], job=job, model=model, kind='gateway_504_estimate',
                                calls_504=n504[key], dollars_list_est=round(el, 4), dollars_proxy_est=round(ep, 4), first=first[key], last=last[key],
                                basis='mean cost of the same %s completed calls' % ('job and model' if ok.get(key) else 'model'),
                                note='504 gateway timeouts at the proxy carry no usage; priced as if the upstream billed the whole call (upper bound)')) + '\n')
print('504 total est_list=%.3f est_proxy=%.3f' % tuple(tot))
for k, v in sorted(other.items()): print('nocost', k, v)
