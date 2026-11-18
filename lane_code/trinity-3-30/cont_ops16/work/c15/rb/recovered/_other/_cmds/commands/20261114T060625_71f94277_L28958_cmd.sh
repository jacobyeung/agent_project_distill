<!-- recovered by seal_plan: transcript=71f94277 line=28958 utc=2026-11-14T06:06:25.729Z kind=commands original_path=(bash command)  -->
K=/scratch/jjyeung/orch_cd/if_p0/out/tree_provenance_v3/kit_ifp0_orchard_job_8d5bdd730bebb9b3; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$K/evidence/orchard_job_assets.json" <<'EOF'
import json, sys
a = json.load(open(sys.argv[1]))
print(list(a.keys())[:30])
s = a.get("small")
print("small:", json.dumps(s)[:700])
sm = a.get("small_members")
print("small_members:", json.dumps(sm)[:1500] if sm else None)
EOF