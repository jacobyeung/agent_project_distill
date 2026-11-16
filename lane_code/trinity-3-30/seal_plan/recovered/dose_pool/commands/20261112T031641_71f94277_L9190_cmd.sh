<!-- recovered by seal_plan: transcript=71f94277 line=9190 utc=2026-11-12T03:16:41.645Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd/dose_pool; cut -c1-700 events/20261111T2120Z_RESULT_T1_removable.md | head -10; ls out/t1_gt 2>/dev/null | head -8; python3 - <<'EOF'
import json,os
for n in ('BUILD_H1.json','BUILD_H2.json'):
    p='/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/'+n
    if os.path.exists(p):
        d=json.load(open(p)); print(n, type(d).__name__, (list(d.keys())[:8] if isinstance(d,dict) else len(d)))
        s=json.dumps(d)[:500]; print(s)
EOF