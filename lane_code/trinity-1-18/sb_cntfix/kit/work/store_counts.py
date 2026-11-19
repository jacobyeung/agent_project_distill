"""Lane sb_countdesign: answer distribution of store v7's object_counting rows (all rows of the family index ranges), by trace form.
Read-only on /scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7. Writes STORE_V7_COUNT_DIST.json."""
import json, re, sqlite3, collections
S = '/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7'
F = json.load(open(S + '/FAMILY_INDEX_RANGES.json'))['families']['object_counting']
con = sqlite3.connect('file:%s/vqa/rows.sqlite?mode=ro' % S, uri=True)
dist = collections.defaultdict(collections.Counter); n = 0; ex = {}
for a, b in F:
    for i, row, target in con.execute('select i,row,target from rows where i between ? and ?', (a, b)):
        d = json.loads(row); q = d['student_input']['question']; ncat = len(re.findall(r'\(s\)', q))
        try: ans = int(float(d['answer']))
        except Exception: continue
        t = target if isinstance(target, str) else ''
        form = 'list' if re.search(r'first appear|first-seen frame|by first appearance|at its first appearance', t) else ('procedure' if re.search(r'count (each|it) once|count each once', t, re.I) else 'other')
        key = ('single' if ncat == 1 else 'multiple', form); dist[key][min(ans, 12)] += 1; n += 1
        ex.setdefault(key, t[:300])
print('rows', n)
out = {}
for key, c in sorted(dist.items()):
    tot = sum(c.values()); ge5 = sum(v for k, v in c.items() if k >= 5); ge4 = sum(v for k, v in c.items() if k >= 4)
    print(key, 'rows', tot, 'answer>=4: %d (%.1f%%)' % (ge4, 100.0 * ge4 / tot), 'answer>=5: %d (%.1f%%)' % (ge5, 100.0 * ge5 / tot), 'hist', sorted(c.items()))
    out['|'.join(key)] = dict(rows=tot, ge4=ge4, ge5=ge5, hist=sorted(c.items()), example=ex[key])
json.dump(out, open('STORE_V7_COUNT_DIST.json', 'w'), indent=1)
