<!-- recovered by seal_plan: transcript=71f94277 line=27419 utc=2026-11-14T01:40:07.218Z kind=commands original_path=(bash command)  -->
M=/scratch/jjyeung/orch_cd/evalx/work/milestone; cat $M/STEP200_LAUNCHER.diff; echo ---; sha256sum $M/STEP200_LAUNCHER.diff | cut -c1-16; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json,hashlib
v=json.load(open('$M/STEP200_LAUNCHER_REVIEW_REQUEST.json'))
print(json.dumps(v)[:1500])
"; echo; tail -n 4 $M/STEP200_LAUNCHER_TESTS.log | cut -c1-200