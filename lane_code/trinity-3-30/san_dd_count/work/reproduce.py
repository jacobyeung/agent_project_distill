#!/usr/bin/python3
"""Lane san_dd_count: reprints the numbers REPORT.md rests on. Read-only; run with /usr/bin/python3 (about 10 s)."""
import sys, json, re, random, sqlite3
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_count/work'); import cnt as C
from collections import Counter, defaultdict
def num(x):
    try: return float(x)
    except Exception: return None
# 1. Undercount at truth 3 (step 200, non-runaway, single-category first-seen lists): the list stops at two entries
n2 = tot = 0
for s in ['dev-S1', 'R0-dev']:
    for r in C.load('R1', 200, s):
        if r['forced_close'] or r['subtype'] == 'multiple' or r['P']['form'] != 'FS': continue
        if num(r['gt']) == 3 and num(r['pred']) < 3:
            tot += 1; n2 += len(r['P']['lists'][0]) == 2
print('1. truth-3 undercounts at step 200 whose list stops at two entries: %d of %d' % (n2, tot))
# 2. Training prior: share of single-category counting rows answering 2 (seeded primary-key sample of 1,500)
F = json.load(open('/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json'))['families']['object_counting']
ids = [i for a, b in F for i in range(a, b + 1)]
random.seed(20261119); samp = sorted(random.sample(ids, 1500))
con = sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro', uri=True)
rows = []
for k in range(0, 1500, 200):
    rows += [json.loads(t) for _, t in con.execute('select i,row from rows where i in (%s)' % ','.join(map(str, samp[k:k + 200])))]
single = [d for d in rows if len(re.findall(r'\(s\)', d['student_input']['question'])) == 1]
multi = [d for d in rows if len(re.findall(r'\(s\)', d['student_input']['question'])) > 1]
print('2. sampled single-category training rows answering 2: %d of %d' % (sum(str(d['answer']) == '2' for d in single), len(single)))
low = sum(int(float(d['answer'])) == len(re.findall(r'\(s\)', d['student_input']['question'])) for d in multi)
R0 = C.load('R1', 200, 'R0-dev'); M = [r for r in R0 if r['subtype'] == 'multiple']
print('3. sampled multi-category training rows whose total equals the number of categories: %d of %d; R0-dev multiple items with truth 2: %d of %d'
      % (low, len(multi), sum(r['gt'] == '2' for r in M), len(M)))
# 4. R0-dev multiple, truth 2, non-runaway overcounts: which category list is inflated
first = over = 0; cost = 0.0
for r in M:
    if r['forced_close'] or r['P']['form'] != 'FS' or r['gt'] != '2' or num(r['pred']) <= 2: continue
    over += 1; cost += 1 - r['score']; first += len(r['P']['lists'][0]) > 1
print('4. R0-dev multiple truth-2 overcounts with the first-named category inflated: %d of %d (cost %.2f R0-dev points)' % (first, over, 100 * cost / len(R0)))
# 5. Relative count, step 200, force-closed: the forced answer calls the looping category the larger one
def word(r, l): return {o.split('. ', 1)[0]: o.split('. ', 1)[1] for o in r['options']}.get((l or '').strip())
def subj(q):
    cs = C.cats(q)
    return (cs[1], cs[0]) if q.startswith('In comparison with') else (cs[0], cs[-1])
rel = C.load('R1', 200, 'dev-S1', types=('relative_count',)); fc = [r for r in rel if r['forced_close']]
agree = right = 0
for r in fc:
    s, ref = subj(r['question'])
    lines = [l for l in C.think(r['text'])[:6000].split('\n') if l.startswith('Step')]
    h = re.match(r'Step \d+:\s*([^:]*)', lines[-1]).group(1) if lines else ''
    a, b = s.split()[-1] in h, ref.split()[-1] in h
    exp = 'more' if a and not b else ('fewer' if b and not a else None)
    if exp and word(r, r['pred']) == exp: agree += 1; right += r['score'] == 1
print('5. relative-count force-closed items whose answer calls the looping category the larger: %d of %d; right on %d of %d' % (agree, len(fc), right, agree))
# 6. Runaway items at step 200 scored under the step-544 form (count stated before the first-seen frames)
for s in ['dev-S1', 'R0-dev']:
    D = {ck: {r['id']: r for r in C.load(*ck, s)} for ck in [('S1', 544), ('R1', 200)]}
    ru = [i for i, r in D[('R1', 200)].items() if r['forced_close']]
    a = sum(D[('R1', 200)][i]['score'] for i in ru); b = sum(D[('S1', 544)][i]['score'] for i in ru)
    print('6. %s: %d runaway items at step 200 score %.1f there and %.1f at step 544 (set-level difference %+.2f points)'
          % (s, len(ru), 100 * a / len(ru), 100 * b / len(ru), 100 * (b - a) / len(D[('R1', 200)])))
# 7. dev-S1 room/category groups whose truths disagree: are the items on different scans?
raw = {}
for l in open('/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/x/main/a0/results/0/items_a0.jsonl'):
    d = json.loads(l)
    if d['question_type'] == 'object_counting': raw[d['id']] = d.get('scene_name')
dv = {r['id']: r for r in C.load('R1', 200, 'dev-S1')}; g = defaultdict(list)
for i, r in dv.items(): g[(r['room'], C.cats(r['question'])[0])].append(i)
conf = [v for v in g.values() if len(set(dv[i]['gt'] for i in v)) > 1]
same = sum(1 for v in conf if len(set(raw[i] for i in v)) < len(v))
print('7. conflicting dev-S1 room/category groups: %d of %d (%d items); groups with two items on the same scan: %d; their step-200 loss %.2f points'
      % (len(conf), len(g), sum(map(len, conf)), same, 100 * sum(1 - dv[i]['score'] for v in conf for i in v) / len(dv)))
