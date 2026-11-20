K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%T; wc -l out/45_v6p30.jsonl out/46_v6v30.jsonl out/47_v6p30argmed.jsonl out/48_v6p30astra.jsonl queue/46_v6v30.jsonl; cat faults/45_v6p30.gaveup.jsonl
tail -2 v6/chain.log; tmux kill-session -t nvk2_chain && echo killed_nvk2_chain; tmux ls
cat > $K/kit/est504.py <<'PYEOF'
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
PYEOF
$P -B kit/ledger.py nvkey2 '{"45_v6p30": "V6 O3 gate, form v2 (L/M/S/A states, points on L and M) primary, Argon high, on the first 30 K1 training captures (FIRST30 ba5bd11b); calibration against rasters; the form failed its gate (RESULT 0530Z)", "46_v6v30": "V6 O3 gate, form v2 verifier, Astra high, chained on the primaries of 45 (names and counts, no points); calibration against rasters", "47_v6p30argmed": "V6 O3 paired variant: form v2 primary at Argon medium effort on the same 30 captures; calibration", "48_v6p30astra": "V6 O3 paired variant: form v2 with Astra high as the primary on the same 30 captures; calibration"}'
$P -B kit/est504.py nvkey3 all
$P -B - <<'PY'
import json, sys, glob, importlib.machinery, collections, statistics as st
sys.path.insert(0, 'kit')
import score_v1 as N
O = importlib.machinery.SourceFileLoader('old', 'kit/score_v1.py.edb231716210').load_module()
for fn in sorted(glob.glob('out/*.jsonl')) + sorted(glob.glob('analysis_only/out/*.jsonl')):
    n = o = w = 0; N.PARSE_STATS.clear(); bad = []
    for l in open(fn):
        try: r = json.loads(l)
        except Exception: continue
        if not isinstance(r, dict) or 'text' not in r: continue
        n += 1; a = O.parse(r['text']) is not None; b = N.parse(r['text']) is not None; o += a; w += b
        if a and not b: print('REGRESSION', fn, r['id'][:24])
        if not b: bad.append(r)
    print('%-44s n=%3d old_ok=%3d new_ok=%3d %s' % (fn, n, o, w, dict(N.PARSE_STATS)))
    if fn.split('/')[-1][:2] in ('45', '46', '47', '48'):
        for r in bad[:4]:
            t = (r['text'] or '').strip()
            try: json.loads(t[t.find('{'):])
            except Exception as e: print('   FAIL', r['id'][:22], r.get('finish'), len(t), str(e)[:60], repr(t[max(0, getattr(e, 'pos', 0) - 70):getattr(e, 'pos', 0) + 30]))
lat = collections.defaultdict(list); fin = collections.Counter(); keys = None
for l in open('meter/CALLS.jsonl'):
    r = json.loads(l); keys = keys or sorted(r)
    if r['job'][:2] in ('10', '30', '50', '52', '45', '46', '47', '48'):
        if r.get('status') == 200 and r.get('latency_s'): lat[(r['job'], r['model'].split('/')[-1])].append(r['latency_s'])
        fin[(r['job'], r['model'].split('/')[-1], r.get('status'), r.get('finish'))] += 1
print('CALLS keys', keys)
for k, v in sorted(lat.items()): print('lat', k, 'n', len(v), 'median', round(st.median(v)), 'p90', round(sorted(v)[int(0.9 * len(v)) - 1]), 'max', round(max(v)))
for k, v in sorted(fin.items()): print('fin', k, v)
PY
ls /scratch/jjyeung/k1_frames | head -3; ls /scratch/jjyeung/k1_frames | wc -l; $P -c "import json; d=json.load(open('$K/k1r/k1r_index.json')); print('k1r index', len(d)); import itertools; print(list(itertools.islice(d.items(), 1)))"
cat meter/METER.json; echo; tail -3 runner.log
