"""Q2: object order in 600 toward rows (store v7, PK sample seed 7 then 11) and in the R0-dev / dev-S1 questions."""
import json, sqlite3, random, re, collections, sys
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dirtw/work'); from tw_lib import K, T
F = json.load(open('/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json'))['families']
ids = []
for t in T:
    for a, b in F[t]: ids.extend(range(a, b + 1))
random.seed(7); S = sorted(random.sample(ids, 2000))
con = sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro', uri=True)
AWAY = re.compile(r"opposite direction|away from|back to the|my back to|your back to|behind you", re.I)
N = r"the ([a-z0-9][a-z0-9 '\-/]*?)"
OBS = re.compile(r"(?:standing|stand|position(?:ed)?|placed|located|be|am)\s+(?:right\s+)?(?:by|beside|next to|at|near|close to)\s+" + N + r"(?=,| and | with |\.|;| facing| looking)", re.I)
OBS2 = re.compile(r"(?:From|from)\s+(?:beside|next to|by|a position beside|a spot beside|a position next to)\s+" + N + r"(?=,| I | look| you)", re.I)
FAC = re.compile(r"(?:facing|face|faces|look toward|looking toward|look towards|looking at|look at|turned toward|turn toward|oriented toward|pointed at)\s+(?:toward |towards )?" + N + r"(?=,|\.|;| and |\?| from)", re.I)
FAC2 = re.compile(r"with " + N + r" (?:ahead of|in front of|straight ahead)", re.I)
TGT = re.compile(r"(?:is|describes|Where is|where is|lies|locate)\s+" + N + r"(?= to | on | relative| located|:| lie| in |\?| positioned| from| when)", re.I)
TGT2 = re.compile(r"(?:right|back|behind|left)[,]? is " + N + r"\?", re.I)
def roles(q):
    q = q.split('\n')[0]; out = {}
    for k, pats in (('O', (OBS, OBS2)), ('F', (FAC, FAC2)), ('T', (TGT2, TGT))):
        for p in pats:
            m = p.search(q)
            if m: out[k] = (m.start(1), m.group(1).lower()); break
    return out
def order(q):
    r = roles(q)
    if len(r) < 3: return None
    return ''.join(k for k, v in sorted(r.items(), key=lambda x: x[1][0]))
rows = []
for k in range(0, 2000, 200):
    for i, r in con.execute('select i,row from rows where i in (%s)' % ','.join(map(str, S[k:k + 200]))):
        j = json.loads(r); q = j['student_input']['question']
        if not AWAY.search(q.split('\n')[0]): rows.append((i, j.get('pool'), q))
random.seed(11); T6 = random.sample(rows, 600)
oc = collections.Counter(); bad = []; ex = {}
for i, p, q in T6:
    o = order(q); oc[o] += 1
    if o is None and len(bad) < 6: bad.append(q.split('\n')[0][:170])
    if o and o != 'OFT': ex.setdefault(o, (i, p, q.split('\n')[0][:200]))
print('toward rows in the 2,000 sample:', len(rows), '; order in 600:', oc.most_common())
for k, v in ex.items(): print('  non-OFT', k, v)
for b in bad: print('  unparsed:', b)
for st in ('R0-dev', 'dev-S1'):
    rr = K.direct('R1', 200, st, types=T); c = collections.Counter(); cw = collections.Counter()
    for r in rr:
        if AWAY.search(r['question'].split('\n')[0]): continue
        c[order(r['question'])] += 1
        cw[re.sub(N, 'the X', r['question'].split('\n')[0])[:100]] += 1
    print(st, 'toward questions, order:', c.most_common(), '; templates:', len(cw)); [print('   ', v, k) for k, v in cw.most_common(4)]
