<!-- recovered by seal_plan: transcript=71f94277 line=24863 utc=2026-11-13T20:30:42.709Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/orchard_cp2; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/logs/production_last.json <<'EOF'
import json, sys, datetime
j = json.load(open(sys.argv[1]))
f = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%H:%M:%SZ")
print("SNAP", j["checked_at"][11:19], j["queue"].strip(), "free GB", round(j["project_free_bytes"]/1e9, 1))
m = j.get("metrics", {}).get("metrics_169097.jsonl", {})
print("metrics bytes", m.get("bytes"), "mtime", f(m.get("mtime", 0)), {k: v for k, v in m.items() if k not in ("first_line", "tail", "bytes", "mtime")})
g = j["logs"].get("169097.gpu", {})
print("gpu", f(g.get("mtime", 0)), g.get("tail", "")[-150:].replace("\n", " | "))
for k in j:
    if "step" in k.lower() or "donor" in k.lower() or "train" in k.lower():
        print(k, ":", json.dumps(j[k])[:400])
EOF