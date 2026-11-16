<!-- recovered by seal_plan: transcript=71f94277 line=22597 utc=2026-11-13T16:28:52.315Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/orchard_cp2; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/out/production_169097/20261113T162458Z.json <<'EOF'
import json, sys
j = json.load(open(sys.argv[1]))
print(json.dumps(j["rate_probe"]["receipt"]["body"], indent=0)[:1800])
t = j["logs"]["169097.out"]["tail"]
print("OUT TAIL:", t[-700:])
EOF