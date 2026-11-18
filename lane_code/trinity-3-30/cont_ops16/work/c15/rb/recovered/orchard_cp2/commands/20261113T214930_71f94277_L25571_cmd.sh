<!-- recovered by seal_plan: transcript=71f94277 line=25571 utc=2026-11-13T21:49:30.504Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/orchard_cp2; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/logs/production_last.json <<'EOF'
import json, sys
j = json.load(open(sys.argv[1]))
m = j.get("metrics", {}).get("metrics_169097.jsonl", {})
print("SNAP", j["checked_at"][11:19], j["queue"].strip(), "free GB", round(j["project_free_bytes"]/1e9, 1))
print("summary", json.dumps(m.get("summary"))[:400])
print("steps tail:", j["logs"]["169097.steps"]["tail"][-230:].replace("\n", " | "))
print("gcs tail:", j["logs"].get("gcs.log", {}).get("tail", "")[-330:].replace("\n", " | "))
EOF