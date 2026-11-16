<!-- recovered by seal_plan: transcript=71f94277 line=22070 utc=2026-11-13T14:51:57.819Z kind=commands original_path=(bash command)  -->
D=/scratch/jjyeung/orch_cd/legs1_dbs/ap/5e1d07a4/f/h/r16/rows.sqlite; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$D" <<'EOF'
import sqlite3, sys, json, collections, random
con = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
r = json.loads(con.execute("select row from rows where i=(select min(i) from rows)").fetchone()[0])
print("keys:", {k: (type(v).__name__, (len(v) if hasattr(v, '__len__') else v)) for k, v in r.items()})
# type census on a spread sample
random.seed(0)
n = con.execute("select max(i) from rows").fetchone()[0]
cnt = collections.Counter()
ids = random.sample(range(1, n + 1), 3000)
for (row,) in con.execute("select row from rows where i in (%s)" % ",".join(map(str, ids))):
    j = json.loads(row)
    cnt[(j.get("question_type") or j.get("type") or j.get("task") or j.get("qtype") or "?")] += 1
print(cnt.most_common(12))
EOF