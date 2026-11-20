W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=/scratch/jjyeung/orch_n30/n_review/r1e/tcpp; date -u +%TZ
for h in a1869ae2 969cdb56; do grep -o "\"[^\"]*$h[^\"]*\"" $W/w24m/out/UPLOADS_24M4M.json $W/w24h/out/UPLOADS_24M4H.json $W/w24e/out/UPLOADS_24M4E.json 2>/dev/null | sort -u | head -5; done
ls $T/student_pilot | grep -i -E "dev|withheld|room|exclu" ; sha256sum $T/student_pilot/r2_dev_merged.json 2>/dev/null
ls $W/inputs/rooms 2>&1 | head; sha256sum $W/inputs/rooms/* 2>/dev/null | head
grep -n "969cdb56\|withheld\|a1869ae2" $T/student_pilot/r1_handover.py $T/student_pilot/r2_scene_bindings.py $T/student_pilot/s1_exclusions.py 2>/dev/null | cut -c1-250 | head -20
python3 -c "
import json;d=json.load(open('$T/student_pilot/r2_dev_merged.json'));print(type(d).__name__, list(d)[:10] if isinstance(d,dict) else len(d))" 2>&1 | head -3
