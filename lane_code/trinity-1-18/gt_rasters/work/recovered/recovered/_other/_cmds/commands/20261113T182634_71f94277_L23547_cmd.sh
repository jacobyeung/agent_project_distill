<!-- recovered by seal_plan: transcript=71f94277 line=23547 utc=2026-11-13T18:26:34.373Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/orchard_cp2; date -u +%H:%M:%SZ; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/logs/production_last.json <<'EOF'
import json, sys, datetime
j = json.load(open(sys.argv[1]))
print("SNAP", j["checked_at"], j["queue"].strip(), "free GB", round(j["project_free_bytes"]/1e9, 1))
m = j["metrics"]["metrics_169097.jsonl"]
print("metrics bytes", m["bytes"], "mtime", datetime.datetime.fromtimestamp(m["mtime"], datetime.timezone.utc).strftime("%H:%M:%SZ"))
g = j["logs"].get("169097.gpu", {})
print("gpu bytes", g.get("bytes"), "mtime", datetime.datetime.fromtimestamp(g.get("mtime", 0), datetime.timezone.utc).strftime("%H:%M:%SZ"), "| last:", g.get("tail", "")[-140:].replace("\n", " | "))
for k in ("169097.out", "169097.steps"):
    v = j["logs"][k]; print(k, v["bytes"], datetime.datetime.fromtimestamp(v["mtime"], datetime.timezone.utc).strftime("%H:%M:%SZ"))
EOF
ls -t $C/events | head -n 2; ls -lt --time-style=+%H:%M:%S $C/out | head -n 4 | cut -c1-120