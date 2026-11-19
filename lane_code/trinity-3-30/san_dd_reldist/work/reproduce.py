#!/usr/bin/python3
"""Lane san_dd_reldist: prints the five numbers the report rests on. Read-only; CPU; caches a pickle in /tmp only.
Run: /usr/bin/python3 /scratch/jjyeung/orch_n30/san_dd_reldist/work/reproduce.py"""
import sys, os, json, re, sqlite3, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import rd
T = rd.table(); W = [t for t in T if t['s200'] < 1]
# 1. partition of the 131 wrong step-200 items (precedence e > a > c > b > d > other; rules in rd.flags/primary)
P = collections.Counter(rd.primary(t) for t in W)
print('1. wrong at step 200: %d (dev-S1 %d, R0-dev %d); classes %s' % (len(W), sum(t['set'] == 'dev-S1' for t in W),
      sum(t['set'] == 'R0-dev' for t in W), {('f' if k == 'other' else k): v for k, v in sorted(P.items())}))
# 2. dev-S1 accuracy with / without a candidate counted >=2 by the same room's counting items, steps 544 and 200
S = [t for t in T if t['set'] == 'dev-S1']; y = [t for t in S if t['multi_any']]; n = [t for t in S if not t['multi_any']]
f = lambda L, s: '%d/%d' % (sum(t['s%d' % s] for t in L), len(L))
print('2. dev-S1 multi-instance candidate: step544 %s vs %s; step200 %s vs %s; R0-dev items with a single-class counted name: %d of 279'
      % (f(y, 544), f(n, 544), f(y, 200), f(n, 200), sum(t['multi_any'] for t in T if t['set'] == 'R0-dev')))
# 3. step-200 accuracy by step 544's own endpoint margin (ratio of its endpoint value to the next one), all 429
lo = [t for t in T if t['m544'] < 1.25]; hi = [t for t in T if t['m544'] >= 2.0]
A = [t for t in W if t['d200'] == 1]; R = [t for t in T if t['s200'] == 1]
print('3. step-200 accuracy when 544 margin <1.25: %s; >=2.0: %s; margin<=1.25 among 62 adjacent errors %d, among 298 right %d'
      % (f(lo, 200), f(hi, 200), sum(t['m544'] <= 1.25 for t in A), sum(t['m544'] <= 1.25 for t in R)))
# 4. farthest: far-end vs near-end accuracy in the same 93 rooms; truth rank (1=nearest) on the wrong farthest items
F = [t for t in T if t['ep'] == 'farthest']; C = [t for t in T if t['set'] == 'R0-dev' and t['ep'] == 'closest']
print('4. R0-dev farthest %s vs closest %s at step 200; wrong farthest truth rank (1=nearest) %s'
      % (f(F, 200), f(C, 200), sorted(collections.Counter(t['rk200'] + 1 for t in F if t['s200'] < 1).items())))
# 5. store v7 object_rel_distance census: rows naming a class counted >=2 in the same scene; traces naming an instance
FR = json.load(open('/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json'))['families']
con = sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro', uri=True)
def fetch(ids, cols):
    for k in range(0, len(ids), 200):
        ch = ids[k:k + 200]
        yield from con.execute('select i,%s from rows where i in (%s)' % (','.join("json_extract(row,'%s')" % c for c in cols), ','.join('?' * len(ch))), ch)
cnt = collections.defaultdict(int)
for i, sc, q, a in fetch([i for a, b in FR['object_counting'] for i in range(a, b + 1)], ['$.scene', '$.student_input.question', '$.answer']):
    m = re.search(r'how many (.+?)\(s\)', q or '', re.I) or re.search(r'how many (.+?)(?: are| is| can| do| in |\?)', q or '', re.I)
    if m:
        try: cnt[(sc, rd.sing(m.group(1)))] = max(cnt[(sc, rd.sing(m.group(1)))], int(float(a)))
        except ValueError: pass
scenes = {k[0] for k in cnt}; nrow = withc = multi = inst = far = 0
for i, sc, op, tg, q in fetch([i for a, b in FR['object_rel_distance'] for i in range(a, b + 1)], ['$.scene', '$.student_input.options', '$.target', '$.student_input.question']):
    nrow += 1; names = [x[3:].strip().lower() for x in json.loads(op)]
    m = re.search(r'find the (.+?)(?:,| \(|\s+first|\.)', tg.lower())
    if m: names.append(m.group(1).strip())
    inst += bool(re.search(r'instance|nearest one|closest one|several|multiple|duplicate|the other', tg, re.I)); far += bool(re.search(r'farthest|furthest', q, re.I))
    if sc in scenes:
        withc += 1; multi += any(cnt.get((sc, rd.sing(x)), 0) >= 2 for x in names)
print('5. store v7 rel-distance rows %d: %d of %d with same-scene counting rows name a class counted >=2; traces naming an instance %d; farthest questions %d'
      % (nrow, multi, withc, inst, far))
