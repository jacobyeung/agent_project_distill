D=/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa; ls -la $D < /dev/null; nice -n 10 sha256sum $D/rows.sqlite < /dev/null
T=/scratch/jjyeung/orch_n30/n_review/r1j/t; grep -n "^def _pin" -A6 $T/student_pilot/c1_pose_mix.py < /dev/null
/scratch/jjyeung/envs/p1cpu/bin/python -I - <<'PY'
import sqlite3,json
c=sqlite3.connect('file:/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?mode=ro',uri=True)
print([r for r in c.execute("select name, sql from sqlite_master")])
i,row=c.execute('select i,row from rows where i=0').fetchone(); r=json.loads(row)
print(sorted(r)); print({k:(json.dumps(v)[:120]) for k,v in r.items() if k in ('scene','dataset','source','provenance','scene_id','qid')})
i,row=c.execute('select i,row from rows where i=200000').fetchone(); r=json.loads(row)
print(sorted(r)); print({k:(json.dumps(v)[:160]) for k,v in r.items() if k in ('scene','dataset','source','provenance','scene_id','qid')})
PY
