<!-- recovered by seal_plan: transcript=71f94277 line=32672 utc=2026-11-14T17:26:19.373Z kind=commands original_path=(bash command)  -->
D=/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s23_02/pilot5_failure; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json
d=json.load(open('$D/DIAGNOSIS.json'))
print(json.dumps(d,indent=1)[:3500])
"