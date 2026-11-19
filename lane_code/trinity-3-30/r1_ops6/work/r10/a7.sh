export TZ=UTC; date -u +%T
timeout 200 srun --overlap --jobid 172660 -n1 -N1 timeout -k 5 180 nice -n 19 ionice -c3 bash -c '
S=/tmp/jjyeung/a_6ed2c7aa/root/aws/u/ap/f02f16ad/s
python3 -c "
import json,sqlite3
d=json.load(open(\"$S/a2v3/receipt.json\"))
for k in (\"count\",\"composition\",\"shares\",\"scenes\",\"labels\",\"row_schema\",\"frames\"): print(k, json.dumps(d.get(k))[:900])
for r in (\"a2v3\",\"a3v2\"):
  c=sqlite3.connect(\"file:$S/\"+r+\"/rows.sqlite?mode=ro\",uri=True)
  print(r,[x for x in c.execute(\"select name,sql from sqlite_master\")][:4])
  row=c.execute(\"select * from \"+[x[0] for x in c.execute(\"select name from sqlite_master where type=\x27table\x27\")][0]+\" limit 1\").fetchone()
  print(r,\"row0\",[ (type(v).__name__, (v[:300] if isinstance(v,str) else len(v) if isinstance(v,bytes) else v)) for v in row])
"' 2>&1 | grep -v -i cgroup | head -60
