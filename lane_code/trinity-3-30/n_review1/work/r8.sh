W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; D=/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa
cat $D/MANIFEST.json $D/JOB_PATHS.json; echo
nice -n 10 python3 - <<'P'
import sqlite3,json,hashlib,os
db='/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
c=sqlite3.connect('file:'+db+'?mode=ro&immutable=1',uri=True)
for (n,s) in c.execute("select name,sql from sqlite_master"): print(n, s)
for (n,) in c.execute("select name from sqlite_master where type='table'"):
    print(n, c.execute(f"select count(*) from {n}").fetchone())
    r=c.execute(f"select * from {n} limit 1").fetchone(); print(str(r)[:2500])
P
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
for f in ext/pk/remove_0.jsonl ext/pk/remove_3.jsonl w17b/work/build17/inputs/s.json w18/work/build18/inputs/u.json w21/work/build21/inputs/u_union.json inputs/records/n.json inputs/records/z.json w22/work/build22/inputs/naming_remove.json; do echo "== $f $(stat -c %s $W/$f) $(sha256sum < $W/$f | cut -c1-16)"; head -c 400 $W/$f; echo; done
