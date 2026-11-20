"""nvkey3: close the Trinity runner's part of distill_design/NV_SPEND_LEDGER.jsonl after the user's stop: per job, calls, completed calls, 504s,
list and proxy dollars from K/meter/CALLS.jsonl plus the 504 estimates already in the ledger; appends one line of kind trinity_runner_close."""
import json, os, sys, time, collections
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work'); LED = '/data2/jjyeung/agent_project_data/distill_design/NV_SPEND_LEDGER.jsonl'
J = collections.OrderedDict(); first = last = None
for l in open(K + '/meter/CALLS.jsonl'):
    r = json.loads(l); j = J.setdefault(r['job'], collections.Counter()); first = first or r['utc']; last = r['utc']
    j['calls'] += 1; j['ok'] += r.get('status') == 200; j['n504'] += r.get('status') == 504
    j['list'] += r.get('dollars') or 0.0; j['proxy'] += float(r.get('header_cost') or 0)
est = collections.Counter(); estp = collections.Counter()
for l in open(LED):
    try: d = json.loads(l)
    except Exception: continue
    if d.get('kind') == 'gateway_504_estimate': est[d['job']] += d['dollars_list_est']; estp[d['job']] += d['dollars_proxy_est']
jobs = {j: dict(calls=c['calls'], ok=c['ok'], n504=c['n504'], dollars_list=round(c['list'], 4), dollars_proxy=round(c['proxy'], 4),
                est504_list=round(est[j], 4), est504_proxy=round(estp[j], 4)) for j, c in J.items()}
tot = {k: round(sum(v[k] for v in jobs.values()), 4) for k in ('calls', 'ok', 'n504', 'dollars_list', 'dollars_proxy', 'est504_list', 'est504_proxy')}
line = dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), lane='nvkey3', host=os.uname()[1], kind='trinity_runner_close', job='ALL_TRINITY_RUNNER',
            model='all', stop='user stop order (ORCH ORDER 0552Z): no further paid call; credits go to another project', first_call=first, last_call=last,
            jobs=jobs, totals=tot, total_with_504_estimates=dict(list=round(tot['dollars_list'] + tot['est504_list'], 2), proxy=round(tot['dollars_proxy'] + tot['est504_proxy'], 2)),
            note='source K/meter/CALLS.jsonl on trinity-2-28 (every call of the Trinity runner under nvkey1, nvkey2 and nvkey3); Orchard spend is in nv_orch1 lines')
if '--dry' not in sys.argv: open(LED, 'a').write(json.dumps(line) + '\n')
for j, v in jobs.items(): print('%-22s calls %4d ok %4d 504 %2d list %8.3f proxy %8.3f est504 %6.3f' % (j, v['calls'], v['ok'], v['n504'], v['dollars_list'], v['dollars_proxy'], v['est504_list']))
print('TOTAL', json.dumps(tot), 'with 504 estimates', json.dumps(line['total_with_504_estimates']))
