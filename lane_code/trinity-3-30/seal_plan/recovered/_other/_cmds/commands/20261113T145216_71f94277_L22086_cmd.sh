<!-- recovered by seal_plan: transcript=71f94277 line=22086 utc=2026-11-13T14:52:16.380Z kind=commands original_path=(bash command)  -->
D=/scratch/jjyeung/orch_cd/legs1_dbs/ap/5e1d07a4/f/h/r16/rows.sqlite; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$D" <<'EOF'
import sqlite3, sys, json, collections, random
con = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
cnt = collections.Counter(); by = collections.defaultdict(list)
random.seed(11)
for (i, row) in con.execute("select i, row from rows"):
    j = json.loads(row)
    t = j["routing"]["question_type"]
    cnt[(t, j["routing"].get("trace_revision"), j["routing"].get("form"))] += 1
    if random.random() < 0.01:
        by[t].append((i, j))
for k, v in sorted(cnt.items(), key=lambda x: -x[1]): print(v, k)
for t, rows in sorted(by.items()):
    if t == "camera_displacement": rows = rows[:3]
    for i, j in random.sample(rows, min(5, len(rows))):
        print("\n### %s i=%d %s gt=%s" % (t, i, j["scene"], j["routing"].get("gt_answer")))
        print("Q:", j["student_input"]["question"][:400], "| options:", j["student_input"]["options"])
        print("T:", j["target"][:1100])
EOF