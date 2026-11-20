K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
cat > $K/kit/close_ledger.py <<'PYEOF'
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
PYEOF
date -u +%T; wc -l out/60_v6bA_first30.jsonl out/61_v6bN_first30.jsonl out/62_v6bI_first30.jsonl; cat faults/6*.gaveup.jsonl 2>/dev/null | wc -l
$P -B kit/ledger.py nvkey3 '{"60_v6bA_first30": "V6 boolean form (C1 prompt) calibration on the first 30 K1 training captures: named GT classes plus frozen check nouns, Argon high and Astra high; stopped by the user at 06:00Z (partial)", "61_v6bN_first30": "V6 boolean form calibration: naming call (inventory names, aliases, look-alike, flags), both families, first 30 K1 training captures; stopped by the user (partial)", "62_v6bI_first30": "V6 boolean form calibration: presence on the union of both families inventory names plus check nouns, chained; stopped by the user (partial)"}'
$P -B kit/est504.py nvkey3 60_v6bA_first30,61_v6bN_first30,62_v6bI_first30 | tail -3
V6B_TAG=V6B_first30_partial timeout 600 $P -B kit/score_v6b.py out/60_v6bA_first30.jsonl out/62_v6bI_first30.jsonl out/61_v6bN_first30.jsonl > scores/V6B_first30_partial.txt 2>&1; echo "score rc $?"
$P -B -c "
import json; d=json.load(open('scores/V6B_first30_partial.json'))
print('calls', json.dumps(d['calls'])); print('caps', d['captures_A'], d['captures_I'])
for f in ('argon','astra'):
    o=d['named_'+f]; print(f, {k: o[k] for k in ('present_at_1pct','absent_at_0px','present_at_1pct_by_ds','point_in_mask_5pct_plus','point_in_mask_1-5pct')})
t=d['two_family_named']; print('two', {k: t[k] for k in ('facts_both','kept_share','agreed_present_at_1pct','agreed_present_at_1pct_scannet_pp','agreed_absent_at_0px','both_wrong_at_1pct','both_wrong_at_0px','agreed_points_in_mask_5pct_plus')})
print('check', json.dumps(d['check_nouns'])); print('inv', json.dumps(d['inventory'])); print('bars', d['bars'])"
$P -B kit/close_ledger.py
mkdir -p bank && T=bank/nvkey_trinity_bank_20261120.tgz && [ ! -f $T ] && tar czf $T out analysis_only scores meter faults kit runner.log runner.stdout queue queue_done excl c1/C1_MANIFEST.json v6/CHECK_VOCAB.json v6/FIRST30.json v6/R3_SIBLINGS.json v6/chain.log v6b/chain.log v6b/test/A.jsonl v6b/test/score.txt v2/O4_INSTANCES.json v2/O4_ALIAS_CANDIDATES.jsonl $(ls v1/*.json 2>/dev/null) 2>&1 | tail -3
ls -la bank/; sha256sum bank/nvkey_trinity_bank_20261120.tgz; tar tzf bank/nvkey_trinity_bank_20261120.tgz | wc -l
