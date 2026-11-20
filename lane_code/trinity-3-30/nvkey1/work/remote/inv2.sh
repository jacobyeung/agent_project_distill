set +x
cd /scratch/jjyeung
echo "== devs1_frames"; ls devs1_frames | head -8; ls devs1_frames | wc -l; d=$(ls devs1_frames | head -1); [ -d devs1_frames/$d ] && { ls devs1_frames/$d | head -5; ls devs1_frames/$d | wc -l; }
ls -la devs1_frames | head -5
echo "== devs1_r2"; ls devs1_r2 | head -10; ls devs1_r2 | wc -l
echo "== k1"; ls k1 | head -20; for x in $(ls k1 | head -6); do echo "-- k1/$x"; ls k1/$x | head -6; done
echo "== k1_frames count"; find k1_frames -type f | wc -l
echo "== sb_cachk"; ls orch_n30/sb_cachk | head -30; ls orch_n30/sb_cachk/* -d 2>/dev/null | head
echo "== grd_funnel1"; ls orch_n30/grd_funnel1 | head; ls orch_n30/grd_funnel1/* | head -40
echo "== n30_mirror"; ls n30_mirror | head -40
echo "== q3d"; ls orch_n30/q3d_price1 | head
echo "== sqlite"
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import sqlite3
c = sqlite3.connect('file:/scratch/jjyeung/orch_n30/fb_pack/point/out/rows_pointing_locate.sqlite?mode=ro', uri=True)
for (name, sql) in c.execute("select name, sql from sqlite_master where type in ('table','view','index')"):
    print('T', name, (sql or '')[:600])
for (name,) in c.execute("select name from sqlite_master where type='table'"):
    n = c.execute('select count(*) from "%s"' % name).fetchone()[0]; print('N', name, n)
    cur = c.execute('select * from "%s" limit 2' % name); cols = [d[0] for d in cur.description]
    for r in cur.fetchall():
        print('R', name, {k: (v[:300] if isinstance(v, str) else (('<blob %d>' % len(v)) if isinstance(v, (bytes, bytearray)) else v)) for k, v in zip(cols, r)})
PY
