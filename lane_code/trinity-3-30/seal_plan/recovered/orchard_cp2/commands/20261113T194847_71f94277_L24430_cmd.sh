<!-- recovered by seal_plan: transcript=71f94277 line=24430 utc=2026-11-13T19:48:47.540Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/orchard_cp2; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/logs/production_last.json <<'EOF'
import json, sys, datetime
j = json.load(open(sys.argv[1]))
f = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%H:%M:%SZ")
print("SNAP", j["checked_at"][11:19], j["queue"].strip(), "free GB", round(j["project_free_bytes"]/1e9, 1))
L = j["logs"]
for k in ("169097.out", "169097.steps", "169097.gpu", "gcs.log"):
    if k in L: print(k, L[k]["bytes"], f(L[k]["mtime"]), "|", L[k]["tail"][-260:].replace("\n", " | "))
m = j.get("metrics", {}).get("metrics_169097.jsonl", {})
print("metrics", m.get("bytes"), f(m.get("mtime", 0)), {k: v for k, v in m.items() if k in ("step", "last_step", "steps", "last_step_seconds")})
for k in j:
    if k not in ("logs", "preflight", "space_attribution", "project_df", "sacct", "queue", "admission_metadata", "runtime_metadata", "metrics", "checked_at", "job", "kit", "run", "project_free_bytes", "size_reader_tools"):
        print(k, ":", json.dumps(j[k])[:500])
EOF