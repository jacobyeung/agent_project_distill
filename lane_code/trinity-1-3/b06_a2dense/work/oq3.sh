I=/project/community/jjyeung/distill/okit/in/cr
ls -la $I/rt_b8b60bcef027.tar $I/ca8d40ab9b55.p0* $I/57ef13741a40.p0* $I/c855379fcefb.p00 /project/community/jjyeung/okh7/7c9f2d84/ ~/okit/i/eb3429c5/eb3429c5.tar 2>&1
tar tvf $I/rt_b8b60bcef027.tar | head
tar tvf ~/okit/i/eb3429c5/eb3429c5.tar | head -20
cd /tmp && nice -n 19 /project/community/jjyeung/cp4tk_fr/venv/bin/python -I - <<'PY'
import sqlite3,json
c=sqlite3.connect('file:/project/community/jjyeung/okh7/7c9f2d84/rows.sqlite?mode=ro&immutable=1',uri=True)
for r in c.execute("select name,sql from sqlite_master"): print(r)
t=[r[0] for r in c.execute("select name from sqlite_master where type='table'")][0]
cur=c.execute(f"select * from {t} limit 1"); names=[d[0] for d in cur.description]; row=cur.fetchone()
for n,v in zip(names,row): print(n, str(v)[:1200])
PY
