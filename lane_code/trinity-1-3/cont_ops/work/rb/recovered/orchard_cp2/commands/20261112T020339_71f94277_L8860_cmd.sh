<!-- recovered by seal_plan: transcript=71f94277 line=8860 utc=2026-11-12T02:03:39.360Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; grep -n -i -E "k6tk|cp4tk_fr" orchard_cp2/out/ORCHARD_REMOVAL_LIST.md | cut -c1-500 | head -10; python3 - <<'EOF'
import json
d=json.load(open('/scratch/jjyeung/orch_cd/p1c_build/k6/INDEX.json'))
print(type(d).__name__, list(d.keys())[:12] if isinstance(d,dict) else len(d))
s=json.dumps(d)[:900]; print(s)
EOF