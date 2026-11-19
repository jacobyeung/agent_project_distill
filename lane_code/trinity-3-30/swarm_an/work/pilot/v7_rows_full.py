"""Row audit, step 2: fetch the full rows listed by v7_scan.py (/tmp/v7_k1train_rows.jsonl) from store v7, one primary-key lookup each,
and write /tmp/v7_k1train_full.jsonl (i, alias, capture, category, pool, q, options, answer, target, retrace_a2, shas, frame_indices).
audit_build.py reads that file. usage: /usr/bin/python3 v7_rows_full.py"""
import sqlite3, json
db = '/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite'
c = sqlite3.connect('file:' + db + '?mode=ro', uri=True); n = 0
with open('/tmp/v7_k1train_full.jsonl', 'w') as out:
    for l in open('/tmp/v7_k1train_rows.jsonl'):
        h = json.loads(l); i, row = c.execute('select i,row from rows where i=? limit 1', (h['i'],)).fetchone(); r = json.loads(row)
        t = r.get('target') if isinstance(r.get('target'), str) else json.dumps(r.get('target'))
        out.write(json.dumps(dict(i=i, alias=h['alias'], capture=h['capture'], category=h['category'], pool=r.get('pool'), q=r['student_input']['question'],
                  options=r['student_input'].get('options'), answer=r.get('answer'), target=t, retrace_a2=r.get('retrace_a2'),
                  shas=[f['sha256'] for f in r['student_input']['frames']], frame_indices=r['student_input'].get('frame_indices'))) + '\n'); n += 1
print('rows written', n)
