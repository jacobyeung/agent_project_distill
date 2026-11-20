"""nv_orch1 V4 flags (RULING 0516Z): a row is flagged when both Astra and Argon flag it (point rows: off | wrong_name | absent; null rows: visible);
unsure or missing never flags. Doubted share by dataset and size band; continue past 2,000 rows only if both families doubt 10% or more.
usage: score_v4.py ASTRA_OUT ARGON_OUT -> scores/V4_FLAGS.jsonl (one line per judged row) + scores/V4_summary.json"""
import json, sys, gzip, collections, re
W = '/scratch/jjyeung/orch_n30/nv_orch1/work/'
meta = {'r%d' % r['i']: r for r in (json.loads(l) for l in gzip.open(W + 'pointing_meta.jsonl.gz', 'rt'))}
def parse(t):
    t = (t or '').strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    try: return json.loads(t)
    except Exception:
        try: return json.loads(t[t.find('{'):t.rfind('}') + 1])
        except Exception: return None
def load(p):
    v = {}; asked = set()
    for l in open(p):
        r = json.loads(l); d = parse(r['text']) or {}; asked.update(r['meta']['rows'])
        for rid in r['meta']['rows']: v[rid] = str(d.get(rid, 'missing')).lower()
    return v, asked
S, aS = load(sys.argv[1]); A, aA = load(sys.argv[2])
def flag(rid, v):
    return v in ('off', 'wrong_name', 'absent') if meta[rid]['kind'] != 'gt_absent' else v == 'visible'
def band(r): return 'null' if r['kind'] == 'gt_absent' else ('1-5%' if r['area'] < 0.05 else '>=5%')
ds = {'d1': 'scannet', 'd2': 'scannetpp'}
c = collections.defaultdict(collections.Counter); rows = []
for rid in sorted(aS & aA, key=lambda x: int(x[1:])):
    r = meta[rid]; fs, fa = flag(rid, S[rid]), flag(rid, A[rid]); both = fs and fa
    k = (ds.get(r['d'], r['d']), band(r))
    for kk in (k, ('all', 'all'), (k[0], 'all'), ('all', k[1])):
        c[kk]['rows'] += 1; c[kk]['astra'] += fs; c[kk]['argon'] += fa; c[kk]['both'] += both; c[kk]['argon_unsure_or_missing'] += A[rid] in ('unsure', 'missing'); c[kk]['astra_unsure_or_missing'] += S[rid] in ('unsure', 'missing')
    rows.append({'admitted_id': r['qid'], 'store_index': r['i'], 'store': 'c09bb5ca', 'clip': r['scene'], 'frame': r['frame'], 'object': r['label'], 'kind': r['kind'], 'band': band(r),
                 'verdicts': {'astra': S[rid], 'argon': A[rid]}, 'flag_both': both})
with open(W + 'scores/V4_FLAGS.jsonl', 'w') as f:
    for x in rows: f.write(json.dumps(x) + '\n')
summ = {'%s|%s' % k: dict(v, both_share=round(v['both'] / max(1, v['rows']), 4)) for k, v in sorted(c.items())}
summ['rule'] = 'continue past 2,000 only if both-family doubted share >= 10% (panel kill rule, RULING 0516Z)'
json.dump(summ, open(W + 'scores/V4_summary.json', 'w'), indent=1)
for k, v in sorted(c.items()): print(k, dict(v), 'both %.1f%%' % (100 * v['both'] / max(1, v['rows'])))
