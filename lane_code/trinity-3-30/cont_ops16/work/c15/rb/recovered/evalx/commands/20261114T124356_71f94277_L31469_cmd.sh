<!-- recovered by seal_plan: transcript=71f94277 line=31469 utc=2026-11-14T12:43:56.703Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd/evalx/work/milestone/runs/bffa0d6ef; grep -o '"[a-z_]*model[a-z_]*": *"[^"]*"' $R/direct/main/request.json | sort -u | head -n 10; grep -o '"artifact[a-z_0-9]*": *"[^"]*"\|"export[a-z_0-9]*": *"[^"]*"' $R/RELEASE.json | head -n 6; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import json
p='/scratch/jjyeung/orch_cd/evalx/work/milestone/runs/bffa0d6ef/direct/main/results/0/items_leg_m200_main.jsonl'
with open(p) as f:
    for line in f:
        r=json.loads(line)
        if r.get('question_type')=='object_abs_distance':
            print(sorted(r.keys())[:40]); print(r['id'], r.get('model'), len(r.get('token_ids') or []))
            g=r['raw_generation']; k=g.find('<ground'); print(repr(g[k:k+80])); break
EOF