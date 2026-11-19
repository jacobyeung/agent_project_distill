"""Fix-file option A2: every store-v7 relative-distance row (question_type object_rel_distance) as a REMOVE list in
n.json's Removals format (pool, question_type, reason, row_key = qid, scene = dataset/scene). Checks the format on n.json's
own rows first and that no row repeats an n.json or z.json row_key."""
import sqlite3, json, sys
DB = 'file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro'
N = '/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/n.json'; Z = '/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/z.json'
nrows = [json.loads(l) for l in open(N) if l.strip()]; zrows = [json.loads(l) for l in open(Z) if l.strip()]
nmap = {r['row_key']: r for r in nrows}; zkeys = set(r['row_key'] for r in zrows)
con = sqlite3.connect(DB, uri=True)
out = []; fmt_ok = 0; fmt_bad = 0
for (row,) in con.execute('select row from rows'):
    r = json.loads(row); q = r['qid']
    rec = dict(pool=r.get('pool'), question_type=r.get('question_type'), row_key=q, scene='%s/%s' % (r.get('dataset'), r.get('scene')))
    if q in nmap:
        m = nmap[q]; ok = all(m[k] == rec[k] for k in ('pool', 'question_type', 'scene'))
        fmt_ok += ok; fmt_bad += (not ok)
        if not ok and fmt_bad < 3: print('FORMAT MISMATCH', m, rec)
    if r.get('question_type') == 'object_rel_distance':
        rec['reason'] = 'reldist_template_option'
        out.append(rec)
assert not (set(x['row_key'] for x in out) & (set(nmap) | zkeys)), 'overlap with n.json/z.json'
out.sort(key=lambda x: x['row_key'])
with open(sys.argv[1], 'w') as f:
    for x in out: f.write(json.dumps(x, sort_keys=True, separators=(',', ':')) + '\n')
print('n.json rows matched by format', fmt_ok, 'mismatch', fmt_bad, 'of', len(nrows), '| written', len(out))
