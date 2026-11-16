<!-- recovered by seal_plan: transcript=71f94277 line=22403 utc=2026-11-13T15:36:21.245Z kind=commands original_path=(bash command)  -->
F=/scratch/jjyeung/orch_cd/ORCH_STATE_20261111T0935Z.md; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$F" <<'EOF'
import sys
f = sys.argv[1]
s = open(f).read()
old = "LEG-S1 (four streams, no MDG): PRODUCTION GO WRITTEN 14:54Z (orchard_cp2/inbox/20261113T1454Z_ORCH_GO_production_07ca49df_469ddece.md): one submission"
new = "LEG-S1 (four streams, no MDG): PRODUCTION JOB 169097 RUNNING on orchard-community-2 since 2026-11-13T15:25:38Z (wall limit 24 h; records orchard_cp2/out/production_169097/, submission out/PRODUCTION_469ddece_GO1518_SUBMISSION.json; project-space floor 300 GB by my 1518Z ruling, free space series in out/production_169097/project_free.jsonl). GO 14:54Z (orchard_cp2/inbox/20261113T1454Z_ORCH_GO_production_07ca49df_469ddece.md): one submission"
assert s.count(old) == 1
open(f, "w").write(s.replace(old, new))
print("ok")
EOF