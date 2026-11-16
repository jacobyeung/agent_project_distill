<!-- recovered by seal_plan: transcript=71f94277 line=22076 utc=2026-11-13T14:52:06.983Z kind=commands original_path=(bash command)  -->
D=/scratch/jjyeung/orch_cd/legs1_dbs/ap/5e1d07a4/f/h/r16/rows.sqlite; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$D" <<'EOF'
import sqlite3, sys, json, collections, random
con = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
random.seed(7)
n = con.execute("select max(i) from rows").fetchone()[0]
ids = random.sample(range(1, n + 1), 4000)
by = collections.defaultdict(list)
cnt = collections.Counter()
for (i, row) in con.execute("select i, row from rows where i in (%s)" % ",".join(map(str, ids))):
    j = json.loads(row)
    cnt[(j["dataset"], j["category"])] += 1
    by[j["category"]].append((i, j))
print(cnt.most_common(20))
first = True
for cat, rows in sorted(by.items()):
    for i, j in rows[:2]:
        si = j["student_input"]
        if first:
            print("student_input keys:", {k: (type(v).__name__, (len(v) if hasattr(v, '__len__') else v)) for k, v in si.items()})
            print("routing keys:", {k: (str(v)[:80]) for k, v in j["routing"].items()})
            first = False
        q = si.get("question") or si.get("prompt") or si.get("text") or ""
        print("\n### %s i=%d %s %s" % (cat, i, j["dataset"], j["scene"]))
        print("Q:", str(q)[:500])
        print("T:", j["target"][:900])
EOF