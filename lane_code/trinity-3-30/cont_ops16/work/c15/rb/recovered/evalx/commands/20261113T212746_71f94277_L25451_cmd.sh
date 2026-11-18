<!-- recovered by seal_plan: transcript=71f94277 line=25451 utc=2026-11-13T21:27:46.603Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd; date -u +%H:%M:%SZ; for l in orchard_cp2 evalx leg_s1_canary leg_s1_tree if_p0; do echo "$l: $(ls -t $C/$l/events 2>/dev/null | head -n 1)"; done; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/orchard_cp2/logs/production_last.json <<'EOF'
import json, sys, datetime
j = json.load(open(sys.argv[1]))
m = j.get("metrics", {}).get("metrics_169097.jsonl", {})
print("SNAP", j["checked_at"][11:19], j["queue"].strip(), "free GB", round(j["project_free_bytes"]/1e9, 1), "| summary", json.dumps(m.get("summary"))[:300])
print("steps tail:", j["logs"]["169097.steps"]["tail"][-160:].replace("\n", " | "))
EOF