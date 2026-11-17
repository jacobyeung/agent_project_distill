C=/scratch/jjyeung/orch_n30/cont_ops/work/h1read
ls -la $C $C/out 2>&1 | head -40; cat $C/UPLOAD_PLAN.md 2>/dev/null | head -60; find $C -maxdepth 3 -name 'UPLOAD_PLAN*' 2>/dev/null | head
