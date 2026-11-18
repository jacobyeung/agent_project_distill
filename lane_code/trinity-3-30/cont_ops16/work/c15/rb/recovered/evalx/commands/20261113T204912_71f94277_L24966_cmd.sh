<!-- recovered by seal_plan: transcript=71f94277 line=24966 utc=2026-11-13T20:49:12.826Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/evalx; sed -n '12,40p' $C/events/20261113T2046Z_RESULT_detached_launcher_frozen_for_review.md | cut -c1-900; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/work/milestone/ORCHARD_LAUNCHER_REVIEW_REQUEST.json <<'EOF'
import json, sys
j = json.load(open(sys.argv[1]))
for k, v in j.items():
    if isinstance(v, dict):
        print(k, f"({len(v)} keys)")
        for kk, vv in list(v.items())[:12]:
            print("   ", kk.replace("/scratch/jjyeung/orch_cd/evalx/work/milestone/", ""), str(vv)[:70])
    else:
        print(k, str(v)[:200])
EOF