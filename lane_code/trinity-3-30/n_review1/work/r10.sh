cd /scratch/jjyeung/orch_n30/n_review
python3 - <<'P'
import sqlite3,json
c=sqlite3.connect('file:/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?mode=ro&immutable=1',uri=True)
for i in (839,5623,62152):
    r=json.loads(c.execute('select row from rows where i=?',(i,)).fetchone()[0])
    si=r.get('student_input',{}); si.pop('frames',None); si.pop('frame_indices',None)
    print(i, sorted(r)); print(json.dumps(r)[:4000]); print()
P
