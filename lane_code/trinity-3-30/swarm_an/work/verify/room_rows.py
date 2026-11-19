import json, sqlite3, re, statistics as st, collections
P = '/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7'
idx = json.load(open(P + '/FAMILY_INDEX_RANGES.json'))['families']
print('families', sorted(idx)[:20])
rg = idx['room_size_estimation']; keys = [i for a, b in rg for i in range(a, b + 1)]; print('room rows', len(keys))
db = sqlite3.connect('file:' + P + '/vqa/rows.sqlite?mode=ro', uri=True); rows = []
for k in range(0, len(keys), 200):
    b = keys[k:k + 200]; rows += [json.loads(t) for _, t in db.execute('select i,row from rows where i in (' + ','.join('?' * len(b)) + ')', b)]
sq = []; ft = 0
for r in rows:
    q = r['student_input']['question'].lower(); a = float(r['answer'])
    if re.search(r'square f(ee|oo)t|sq\.? ?ft', q): ft += 1
    else: sq.append(a)
sq.sort()
print('rows', len(rows), 'square-feet', ft, 'square-metre', len(sq), 'median %.1f p90 %.1f max %.1f' % (st.median(sq), sq[int(.9 * len(sq))], sq[-1]), '>=60:', sum(x >= 60 for x in sq), '>=35:', sum(x >= 35 for x in sq))
print(rows[0]['target'][:420])
