<!-- recovered by seal_plan: transcript=71f94277 line=23173 utc=2026-11-13T17:58:18.000Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/orchard_cp2; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/logs/production_last.json <<'EOF'
import json, sys
j = json.load(open(sys.argv[1]))
print(j.get("checked_at"), (j.get("queue") or "").strip())
for k, v in j["logs"].items():
    t = v.get("tail", "")
    print("==", k, v.get("bytes"))
    print(t[-900:])
for k in j.keys():
    if k not in ("logs", "preflight", "space_attribution", "project_df", "sacct", "queue"):
        s = json.dumps(j[k])
        print(k, ":", s[:300])
EOF