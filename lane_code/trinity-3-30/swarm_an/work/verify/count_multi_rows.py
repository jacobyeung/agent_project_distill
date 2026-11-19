import json, random, sqlite3, re, collections
base = '/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7'
idx = json.load(open(base + '/FAMILY_INDEX_RANGES.json'))['families']
db = sqlite3.connect('file:' + base + '/vqa/rows.sqlite?mode=ro', uri=True)
keys = [i for a, b in idx['object_counting'] for i in range(a, b + 1)]
ks = sorted(random.Random(5).sample(keys, 1200)); rows = []
for s in range(0, len(ks), 200):
    b = ks[s:s + 200]; rows += [json.loads(t) for _, t in db.execute('select i,row from rows where i in (' + ','.join('?' * len(b)) + ')', b)]
multi = [r for r in rows if len(re.findall(r'\(s\)', r['student_input']['question'])) > 1]
h = collections.Counter(); eq = 0
for r in multi:
    k = len(re.findall(r'\(s\)', r['student_input']['question'])); a = int(float(r['answer'])); h[(k, a)] += 1; eq += (a == k)
print('counting rows in store', len(keys), 'sampled', len(rows), 'multi-category', len(multi), 'total == number of categories', eq)
print('categories, total -> rows (lowest totals):', sorted(h.items())[:8])
print(multi[0]['student_input']['question'][:200]); print(multi[0]['target'][:400])
