export TZ=UTC; date -u +%TZ
timeout 200 srun --overlap --jobid 174198 -N1 -n1 bash -s <<'EOS'
R=/tmp/a15_f16_174198/w1; P=$R/w/top/p/q
tail -n 2 $R/log/go.log | cut -c1-200; echo "rc: $(cat $R/log/rc 2>/dev/null)"; tail -c 400 $R/log/q.err; echo
ls -la --time-style=+%H:%M:%S $P/p/frames_* | cut -c1-120
/usr/bin/python3 -B -I - <<'PY'
import sqlite3, glob
for q in glob.glob('/tmp/a15_f16_174198/w1/w/top/p/q/p/frames_*/frame_inventory.sqlite'):
    c=sqlite3.connect('file:'+q+'?mode=ro&immutable=1', uri=True)
    n=c.execute('select count(*) from frames').fetchone()[0]
    nj=c.execute("select count(*) from frames where path like '/tmp/jjyeung/q_22c714e1/p/q/f/%'").fetchone()[0]
    ns=c.execute("select count(*) from frames where path like '/tmp/q_22c714e1/%'").fetchone()[0]
    print('frames', n, 'under second name q/f', nj, 'under first name', ns)
PY
EOS
date -u +%TZ
