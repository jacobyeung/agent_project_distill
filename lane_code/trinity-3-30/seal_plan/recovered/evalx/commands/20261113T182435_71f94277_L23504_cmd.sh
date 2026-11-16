<!-- recovered by seal_plan: transcript=71f94277 line=23504 utc=2026-11-13T18:24:35.475Z kind=commands original_path=(bash command)  -->
P=/scratch/jjyeung/orch_cd/evalx/work/milestone/SCOPED_REVIEW_REQUEST.json; wc -c $P; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $P <<'EOF'
import json, sys
j = json.load(open(sys.argv[1]))
def show(o, d=0):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, dict) and d < 2:
                print("  " * d + f"{k}: ({len(v)} keys)")
                if len(v) <= 14: show(v, d + 1)
                else:
                    for kk in list(v)[:6]: print("  " * (d + 1) + f"{kk}: {json.dumps(v[kk])[:110]}")
                    print("  " * (d + 1) + "...")
            elif isinstance(v, list):
                print("  " * d + f"{k}: [{len(v)}] {json.dumps(v)[:300]}")
            else:
                print("  " * d + f"{k}: {json.dumps(v)[:300]}")
show(j)
EOF