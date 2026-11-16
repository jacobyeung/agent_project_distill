<!-- recovered by seal_plan: transcript=71f94277 line=22635 utc=2026-11-13T16:43:33.973Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/orchard_cp2; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/logs/production_last.json <<'EOF'
import json, sys
j = json.load(open(sys.argv[1]))
print(j.get("checked_at"), j.get("queue"))
for k, v in j["logs"].items():
    print("==", k, v.get("bytes"), v.get("mtime"))
    print(v.get("tail", "")[-1300:])
print([k for k in j.keys()])
EOF