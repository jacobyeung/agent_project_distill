<!-- recovered by seal_plan: transcript=71f94277 line=23450 utc=2026-11-13T18:21:59.205Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/orchard_cp2; for f in $(ls $C/out/production_169097/2026*.json | tail -n 60 | awk 'NR%6==1'); do /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$f" <<'EOF'
import json, sys
j = json.load(open(sys.argv[1]))
L = j["logs"]
m = (j.get("metrics") or {}).get("metrics_169097.jsonl", {})
print(j["checked_at"][11:19], "out", L.get("169097.out", {}).get("bytes"), "steps", L.get("169097.steps", {}).get("bytes"), "gpu", L.get("169097.gpu", {}).get("bytes"), "metrics", m.get("bytes"))
EOF
done; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/logs/production_last.json <<'EOF'
import json, sys
j = json.load(open(sys.argv[1]))
L = j["logs"]; m = (j.get("metrics") or {}).get("metrics_169097.jsonl", {})
print("LAST", j["checked_at"][11:19], "out", L["169097.out"]["bytes"], "steps", L["169097.steps"]["bytes"], "metrics", m.get("bytes"), "free", j["project_free_bytes"])
print(L["169097.out"]["tail"][-500:])
EOF