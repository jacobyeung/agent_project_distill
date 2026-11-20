set +x
K=/scratch/jjyeung/orch_n30/nvkey1/work; P=/scratch/jjyeung/envs/p1cpu/bin/python; cd $K
cat > $K/kit/score_c2.py <<'PYEOF'
"""nvkey1 C2 scoring: two judges (and an optional blind third) on pointing-store rows.
usage: score_c2.py OUT.jsonl [THIRD.jsonl] -> work/scores/C2_audit.json, work/c2/REMOVAL_CANDIDATES.jsonl, work/c2/THIRD_ROWS.json
Doubted: a point row whose object is judged absent or whose ring is judged off the object; an absent row whose object is judged present.
Removal candidate: doubted by both judges. Blind third: judges the candidates (and a control sample) without seeing the other verdicts."""
import json, re, sys, os, collections, random
K = '/scratch/jjyeung/orch_n30/nvkey1/work'
meta = {int(k): v for k, v in json.load(open(K + '/c2_rows_meta.json')).items()}
def parse(t):
    if not t: return None
    t = t.strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    try: return json.loads(t)
    except Exception:
        i, j = t.find('{'), t.rfind('}')
        try: return json.loads(t[i:j + 1])
        except Exception: return None
def tb(x):
    if isinstance(x, bool): return x
    if isinstance(x, str) and x.lower() in ('true', 'false'): return x.lower() == 'true'
    return None
def verdicts(fn):
    V = collections.defaultdict(dict)
    for l in open(fn):
        r = json.loads(l); d = parse(r['text']) or {}; m = r['model'].split('/')[-1]
        for i in r['meta']['rows']:
            a = d.get('r%d' % i)
            if not isinstance(a, dict): V[m][i] = None; continue
            row = meta[i]; pres = tb(a.get('present')); on = tb(a.get('on_object')); nf = tb(a.get('name_fits'))
            if row['kind'] == 'gt_absent': doubt = None if pres is None else pres
            else: doubt = None if (pres is None and on is None) else (pres is False or on is False)
            V[m][i] = dict(doubt=doubt, present=pres, on=on, name_fits=nf, point=a.get('point'))
    return V
def band(r):
    if r['kind'] == 'gt_absent': return 'absent row'
    a = r['area']; return '0.2-1%' if a < 0.01 else ('1-5%' if a < 0.05 else '>=5%')
V = verdicts(sys.argv[1]); models = sorted(V); print('judges', models, {m: len(V[m]) for m in models})
rows = sorted(set(i for m in models for i in V[m]))
res = collections.OrderedDict(); res['rows'] = len(rows); res['judges'] = models
def share(S, f):
    S = [x for x in S if f(x) is not None]; return [round(100.0 * sum(bool(f(x)) for x in S) / len(S), 1), len(S)] if S else None
def ci(S, f, n=2000):
    scenes = sorted(set(meta[i]['scene'] for i in S)); by = collections.defaultdict(list)
    for i in S: by[meta[i]['scene']].append(i)
    rng = random.Random(5); vals = []
    for _ in range(n):
        T = [i for s in (rng.choice(scenes) for _ in scenes) for i in by[s]]; v = share(T, f)
        if v: vals.append(v[0])
    vals.sort(); return [vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]] if vals else None
for m in models:
    f = lambda i, m=m: (V[m].get(i) or {}).get('doubt')
    res['doubted_' + m] = [share(rows, f), ci(rows, f)]
both = lambda i: None if any((V[m].get(i) or {}).get('doubt') is None for m in models) else all(V[m][i]['doubt'] for m in models)
either = lambda i: None if any((V[m].get(i) or {}).get('doubt') is None for m in models) else any(V[m][i]['doubt'] for m in models)
res['doubted_both'] = [share(rows, both), ci(rows, both)]; res['doubted_either'] = [share(rows, either), ci(rows, either)]
agree = [i for i in rows if both(i) is not None]
res['judge_agreement'] = round(100.0 * sum(V[models[0]][i]['doubt'] == V[models[-1]][i]['doubt'] for i in agree) / max(1, len(agree)), 1)
by = collections.defaultdict(list)
for i in rows: by[band(meta[i])].append(i); by['dataset ' + meta[i]['dataset']].append(i)
res['doubted_both_by'] = {k: share(v, both) for k, v in sorted(by.items())}
res['doubted_either_by'] = {k: share(v, either) for k, v in sorted(by.items())}
nf = lambda i: None if any((V[m].get(i) or {}).get('name_fits') is None for m in models) else all(V[m][i]['name_fits'] is False for m in models)
res['name_misfit_both'] = share([i for i in rows if meta[i]['kind'] != 'gt_absent'], nf)
cand = [i for i in rows if both(i)]
os.makedirs(K + '/c2', exist_ok=True)
with open(K + '/c2/REMOVAL_CANDIDATES.jsonl', 'w') as f:
    for i in cand:
        r = meta[i]; pts = [V[m][i].get('point') for m in models if isinstance(V[m][i].get('point'), list) and len(V[m][i].get('point')) == 2]
        f.write(json.dumps(dict(store_index=i, qid=r['qid'], scene=r['scene'], canonical=r['canonical'], kind=r['kind'], label=r['label'], frame=r['frame'], area=r['area'],
                                verdicts={m: V[m][i] for m in models}, corrected_point=[round(sum(p[0] for p in pts) / len(pts)), round(sum(p[1] for p in pts) / len(pts))] if pts else None)) + '\n')
rng = random.Random(20261120); ctrl = rng.sample([i for i in rows if both(i) is False], min(len(cand), len([i for i in rows if both(i) is False])))
json.dump({'candidates': cand, 'controls': ctrl}, open(K + '/c2/THIRD_ROWS.json', 'w'))
res['removal_candidates'] = len(cand); res['third_controls'] = len(ctrl)
if len(sys.argv) > 2:
    T = verdicts(sys.argv[2]); tm = sorted(T)[0]
    keep = lambda i: None if (T[tm].get(i) or {}).get('doubt') is None else (not T[tm][i]['doubt'])
    res['third_model'] = tm; res['third_keeps_of_candidates'] = share(cand, keep); res['third_keeps_of_controls'] = share(ctrl, keep)
print(json.dumps(res, indent=0))
os.makedirs(K + '/scores', exist_ok=True); json.dump(res, open(K + '/scores/C2_audit.json', 'w'), indent=1)
PYEOF
wc -l out/10_bake32.jsonl; $P -B kit/score_c1.py out/10_bake32.jsonl 2>&1 | cut -c1-900
$P - <<'PY'
import json, collections
K='/scratch/jjyeung/orch_n30/nvkey1/work'
t=collections.defaultdict(lambda: collections.Counter())
for l in open(K+'/meter/CALLS.jsonl'):
    r=json.loads(l)
    if r['status']!=200: continue
    m=r['model'].split('/')[-1]+'|'+r['job']; c=t[m]; c['n']+=1; c['in']+=r.get('prompt_tokens',0); c['out']+=r.get('completion_tokens',0); c['rs']+=r.get('reasoning_tokens',0); c['secs']+=r['secs']; c['bytes']+=r['bytes']; c['list']+=r.get('dollars') or 0; c['hdr']+=float(r.get('header_cost') or 0)
for m,c in sorted(t.items()):
    n=c['n']; print('PRICE', m, 'n', n, 'in', c['in']//n, 'out', c['out']//n, 'reason', c['rs']//n, 'secs', round(c['secs']/n,1), 'MB', round(c['bytes']/n/1e6,2), 'list$/call', round(c['list']/n,4), 'hdr$/call', round(c['hdr']/n,4))
PY
cat meter/METER.json
