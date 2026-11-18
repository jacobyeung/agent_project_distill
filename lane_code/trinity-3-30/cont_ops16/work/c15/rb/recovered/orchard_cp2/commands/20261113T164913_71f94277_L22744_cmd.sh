<!-- recovered by seal_plan: transcript=71f94277 line=22744 utc=2026-11-13T16:49:13.548Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/orchard_cp2; ls -lt --time-style=+%H:%M:%S $C/logs | head -n 6; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/logs/production_last.json $C/logs/project_space_last.json <<'EOF'
import json, sys
j = json.load(open(sys.argv[1]))
print("snapshot", j.get("checked_at"))
a = j.get("space_attribution", {})
for k, v in a.items():
    if isinstance(v, dict):
        print(k, {x: v.get(x) for x in ("path", "resolved", "files", "apparent_bytes", "allocated_bytes", "complete", "reason")})
        for b in (v.get("large_or_recent") or [])[:12]:
            print("    ", json.dumps(b)[:260])
try:
    p = json.load(open(sys.argv[2]))
    print("project_space_last:", json.dumps(p)[:1200])
except Exception as e:
    print("no project_space_last", e)
EOF