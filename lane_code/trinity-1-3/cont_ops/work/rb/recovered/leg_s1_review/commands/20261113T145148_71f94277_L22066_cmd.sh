<!-- recovered by seal_plan: transcript=71f94277 line=22066 utc=2026-11-13T14:51:48.161Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd; grep -n -i -E "rows read|five rows|sampled rows|read [0-9]+ rows" $C/leg_s1_review/REVIEW_VERDICT.md | cut -c1-500 | head -n 6; echo ==; find $C/legs1_dbs/ap/5e1d07a4 -maxdepth 5 -type f | head; D=$(find $C/legs1_dbs/ap/5e1d07a4 -maxdepth 5 -name "*.sqlite" | head -n 1); echo "DB=$D"; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$D" <<'EOF'
import sqlite3, sys
con = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
for name, sql in con.execute("select name, sql from sqlite_master where type='table'"):
    print(name, "|", (sql or "")[:600])
    print("  n =", con.execute("select count(*) from %s" % name).fetchone()[0])
EOF