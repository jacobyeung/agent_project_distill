<!-- recovered by seal_plan: transcript=71f94277 line=22645 utc=2026-11-13T16:43:38.555Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/orchard_cp2; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/logs/production_last.json <<'EOF'
import json, sys
j = json.load(open(sys.argv[1]))
print(json.dumps(j["space_attribution"], indent=1)[:3500])
EOF