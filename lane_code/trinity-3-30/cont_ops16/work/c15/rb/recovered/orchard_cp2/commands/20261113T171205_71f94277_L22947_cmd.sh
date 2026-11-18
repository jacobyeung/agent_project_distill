<!-- recovered by seal_plan: transcript=71f94277 line=22947 utc=2026-11-13T17:12:05.936Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/orchard_cp2; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/out/PROJECT_COMMUNITY_TOP_LEVEL_20261113.json <<'EOF'
import json, sys, datetime
j = json.load(open(sys.argv[1]))
ents = j.get("entries") or j.get("top_level") or j
if isinstance(ents, dict):
    print(list(ents.keys())[:12]); ents = ents.get("entries", [])
rows = []
for e in ents:
    if isinstance(e, dict):
        rows.append((e.get("mtime") or 0, e.get("name") or e.get("path"), e.get("owner")))
rows.sort(reverse=True)
print(len(rows), "entries; newest:")
for m, n, o in rows[:10]:
    print(datetime.datetime.utcfromtimestamp(m).strftime("%m-%d %H:%MZ"), n, o)
EOF