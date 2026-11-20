P=/scratch/jjyeung/orch_n30/fb_pack/point/out; ls -la $P | head -30
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import sqlite3
c = sqlite3.connect('file:/scratch/jjyeung/orch_n30/fb_pack/point/out/rows_pointing_locate.sqlite?mode=ro', uri=True)
for (n, s) in c.execute("select name, sql from sqlite_master where type='table'"): print(n, s[:600])
for (n,) in c.execute("select name from sqlite_master where type='table'"):
    print(n, c.execute('select count(*) from "%s"' % n).fetchone())
    r = c.execute('select * from "%s" limit 1' % n).fetchone(); print(str(r)[:1500])
PY
ls /scratch/jjyeung/orch_n30/fb_pack/ | head; ls /scratch/jjyeung/orch_n30/fb_pack/k1point 2>/dev/null | head
