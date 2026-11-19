"""Lane san_dd_dirtw: prints the five numbers the report rests on.  Run: /usr/bin/python3 /scratch/jjyeung/orch_n30/san_dd_dirtw/work/reproduce.py
Reads in place via san_kit (R0-dev, dev-S1 at steps 544, R1-100, R1-200) and store v7 rows by primary key; writes nothing."""
import sys, json, re, random, sqlite3, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dirtw/work'); from tw_lib import *
D = load(); c = D[200]; ids = [i for i, r in c.items() if r['subtype'] == 'toward']
REG = {'easy': ['left', 'right'], 'medium': ['left', 'right', 'back'], 'hard': ['front-left', 'front-right', 'back-left', 'back-right']}
W = [i for i in ids if c[i]['score'] == 0]
AW = [i for i in W if D[544][i]['score'] == 0 and D[100][i]['score'] == 0]
same = [i for i in AW if opt(D[544][i], D[544][i]['pred']) == opt(c[i], c[i]['pred'])]
print('1. R0-dev toward items %d; wrong at step 200: %d; wrong at 544, 100 and 200: %d; same wrong option at 544 and 200: %d' % (len(ids), len(W), len(AW), len(same)))
cls = collections.Counter(); near = {True: [0, 0], False: [0, 0]}
for i in ids:
    r = c[i]; lv = LV[r['type']]; t = opt(r, r['gt']); a = opt(r, r['pred']); ang = angle544(D[544][i]['text'])
    dn = min(adist(ang, l) for o in REG[lv] if o != t for l in sep_lines(lv, t, o))
    near[r['score'] == 0][0] += 1; near[r['score'] == 0][1] += dn <= 25
    if r['score'] == 0:
        ax = axis(lv, t, a); L = sep_lines(lv, t, a); d = min(adist(ang, x) for x in L) if L else None
        cls['d gross' if ax == 'both' else ('a boundary' if d <= 25 else ('b mirrored' if ax == 'side' else 'c front-back'))] += 1
print('2. classes of the %d wrong items: %s' % (len(W), dict(sorted(cls.items()))))
print('3. step-544 angle within 25 degrees of a boundary of the truth region: wrong %d of %d, right %d of %d' % (near[True][1], near[True][0], near[False][1], near[False][0]))
H = [i for i in ids if LV[c[i]['type']] == 'hard']; marg = collections.Counter(opt(c[i], c[i]['pred']) for i in H)
flip = {'left': 'right', 'right': 'left'}; k = 0; em = 0.0; n = 0
for i in H:
    if c[i]['score'] != 0: continue
    t = opt(c[i], c[i]['gt']); f, s = t.split('-'); pred = f + '-' + flip[s]; n += 1
    k += opt(c[i], c[i]['pred']) == pred; em += marg[pred] / sum(v for o, v in marg.items() if o != t)
print('4. hard wrong answers matching the faced<->target exchange (side flipped, front/back kept): %d of %d; uniform chance %.1f; chance from the model\'s own answer marginals %.1f' % (k, n, n / 3, em))
F = json.load(open('/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json'))['families']
con = sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro', uri=True)
dids = [i for t in T for a, b in F[t] for i in range(a, b + 1)]; names = collections.Counter()
for j in range(0, len(dids), 200):
    for (q,) in con.execute("select json_extract(row,'$.student_input.question') from rows where i in (%s)" % ','.join(map(str, dids[j:j + 200]))):
        o = names3(q.lower())
        if None not in o:
            for n in o: names[n] += 1
out = []
for st in ('R0-dev', 'dev-S1'):
    rr = [r for r in K.direct('R1', 200, st, types=T) if (st == 'dev-S1' or r['subtype'] == 'toward') and None not in names3(r['question'].lower())]
    b = collections.defaultdict(lambda: [0, 0.0])
    for r in rr:
        m = min(names[n] for n in names3(r['question'].lower())); k = 'never' if m == 0 else ('1-99 rows' if m < 100 else '>=100 rows')
        b[k][0] += 1; b[k][1] += r['score']
    out.append('%s %s' % (st, ', '.join('%s: %.1f%% of %d' % (k, 100 * v[1] / v[0], v[0]) for k, v in sorted(b.items()))))
print('5. score@200 by the rarest object name\'s count in all %d store v7 direction questions: %s' % (len(dids), ' | '.join(out)))
