"""R0-dev and dev-S1 toward object names against the names of all 93,370 store v7 direction questions (json_extract by primary key, 200 per query)."""
import sys, json, sqlite3, collections; sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dirtw/work'); from tw_lib import *
F = json.load(open('/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json'))['families']
con = sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro', uri=True)
dids = [i for t in T for a, b in F[t] for i in range(a, b + 1)]; names = collections.Counter(); unparsed = 0
for k in range(0, len(dids), 200):
    for (q,) in con.execute("select json_extract(row,'$.student_input.question') from rows where i in (%s)" % ','.join(map(str, dids[k:k + 200]))):
        o = names3(q.lower())
        if None in o: unparsed += 1; continue
        for n in o: names[n] += 1
print('direction questions', len(dids), 'unparsed', unparsed, 'distinct names', len(names))
for st in ('R0-dev', 'dev-S1'):
    rr = [r for r in K.direct('R1', 200, st, types=T) if (st == 'dev-S1' or r['subtype'] == 'toward')]
    b = collections.defaultdict(lambda: [0, 0.0])
    for r in rr:
        o = names3(r['question'].lower())
        if None in o: continue
        m = min(names[n] for n in o); k = '0' if m == 0 else ('1-99' if m < 100 else '>=100')
        b[k][0] += 1; b[k][1] += r['score']
    print(st, 'rarest name count over all direction rows:', {k: '%d items, %.1f%%' % (v[0], 100 * v[1] / v[0]) for k, v in sorted(b.items())})
