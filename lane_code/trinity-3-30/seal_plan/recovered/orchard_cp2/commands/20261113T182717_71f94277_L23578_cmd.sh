<!-- recovered by seal_plan: transcript=71f94277 line=23578 utc=2026-11-13T18:27:17.218Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/orchard_cp2; until /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json,sys
j=json.load(open('$C/logs/production_last.json'))
sys.exit(0 if j['checked_at'][11:16] >= '18:31' else 1)" 2>/dev/null; do sleep 20; done; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/logs/production_last.json <<'EOF'
import json, sys, datetime
j = json.load(open(sys.argv[1]))
f = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%H:%M:%SZ")
print("SNAP", j["checked_at"], j["queue"].strip(), "free GB", round(j["project_free_bytes"]/1e9, 1))
m = j["metrics"]["metrics_169097.jsonl"]
print("metrics bytes", m["bytes"], "mtime", f(m["mtime"]))
g = j["logs"].get("169097.gpu", {})
print("gpu bytes", g.get("bytes"), "mtime", f(g.get("mtime", 0)), "| last:", g.get("tail", "")[-150:].replace("\n", " | "))
EOF