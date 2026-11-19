"""Census of every direction row in store v7 (read by primary key, 200 ids per query, nothing copied). Writes work/census_agg.json."""
import json, sqlite3, re, sys, ast, collections, random, statistics
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dir/work'); import dirparse as P
S = '/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7'
F = json.load(open(S + '/FAMILY_INDEX_RANGES.json'))['families']
db = sqlite3.connect('file:' + S + '/vqa/rows.sqlite?mode=ro', uri=True)
AWAY = re.compile(r"away from|opposite direction|my back to|back turned|turned away", re.I)
agg = collections.defaultdict(collections.Counter)
spac = collections.defaultdict(list); vocab = collections.defaultdict(collections.Counter)
samples = collections.defaultdict(list); rnd = random.Random(7)
def lit(x):
    if isinstance(x, (dict, list)): return x
    try: return ast.literal_eval(x)
    except Exception:
        try: return json.loads(x)
        except Exception: return {}
for t in P.T:
    lv = P.LV[t]
    ids = [i for lo, hi in F[t] for i in range(lo, hi + 1)]
    for k in range(0, len(ids), 200):
        for i, row in db.execute('select i,row from rows where i in (%s)' % ','.join(map(str, ids[k:k + 200]))):
            r = json.loads(row); si = lit(r.get('student_input')); rt = lit(r.get('retrace'))
            fam = '%s|%s|%s' % (lv, r.get('pool'), (rt or {}).get('rule') if isinstance(rt, dict) else rt)
            q = si.get('question', ''); opts = si.get('options') or []
            tgt = r.get('target') or ''
            think = tgt.split('<think>', 1)[-1].split('</think>', 1)[0].strip()
            pr = P.parse(dict(type=t, text=think + '</think>'))
            clause = 'away' if AWAY.search(q) else 'toward'
            tmpl = 'R0' if q.startswith('If I am standing by the') else 'para'
            ans = str(r.get('answer'))
            aw = next((o[2:].strip().lower() for o in opts if o.startswith(ans + '.')), None)
            ac = P.code_of_word(aw, lv)
            A = agg[fam]
            A['n'] += 1; A['tmpl_' + tmpl] += 1; A['clause_' + clause] += 1
            A['open_%s_%s_%s' % (pr['open'], clause, pr['turn'])] += 1
            A['verb_%s' % pr['open_verb']] += 1
            A['fwd_%s_%s' % (clause, pr['fwd'])] += 1; A['ans_%s_%s' % (clause, ac)] += 1
            A['fin_eq_ans'] += int(pr['fin'] == ac)
            A['impl_eq_ans'] += int(P.implied(pr['fwd'], lv, pr['turn'] == 'half') == ac)
            A['has135'] += int('135' in think); A['frames_cited'] += int(bool(pr['frames'])); A['inq'] += int(pr['inq'])
            A['digit_nonframe'] += int(bool(re.search(r"\d", re.sub(r"frame \d+", "", think))))
            fi = si.get('frame_indices') or []; fps = si.get('fps')
            if fi and fps and len(fi) > 1: spac[fam].append((fi[-1] - fi[0]) / (len(fi) - 1) / float(fps))
            tr = P.triple(q)
            if tr:
                for o in tr[:3]: vocab[lv][o] += 1
            sc = str(r.get('scene'))
            A['ds_%s' % r.get('dataset')] += 1
            if len(samples[fam]) < 6 or rnd.random() < 0.002:
                samples[fam].append(dict(i=i, qid=r.get('qid'), q=q, opts=opts, ans=ans, target=think, scene=sc))
out = dict(agg={k: dict(v) for k, v in agg.items()},
           spacing={k: dict(n=len(v), median=round(statistics.median(v), 3), p10=round(sorted(v)[len(v) // 10], 3), p90=round(sorted(v)[9 * len(v) // 10], 3)) for k, v in spac.items() if v},
           vocab={k: dict(v.most_common()) for k, v in vocab.items()},
           samples={k: v[:12] for k, v in samples.items()})
json.dump(out, open('/scratch/jjyeung/orch_n30/san_dd_dir/work/census_agg.json', 'w'))
for k in sorted(out['agg']):
    a = out['agg'][k]; print(k, 'n', a['n'], {x: y for x, y in sorted(a.items()) if x.startswith(('tmpl', 'clause', 'open', 'verb', 'ds_')) or x in ('has135', 'frames_cited', 'inq', 'fin_eq_ans', 'impl_eq_ans', 'digit_nonframe')})
for k, v in sorted(out['spacing'].items()): print('spacing', k, v)
