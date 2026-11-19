T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1; cd $T
grep -rn "store_hashes" --include=*.py student_pilot launch_r1 | grep -v tests | head -30
echo ==== r1_rooms; wc -l student_pilot/r1_rooms.py; sed -n 1,220p student_pilot/r1_rooms.py
echo ==== K1R0 keys; python3 -c "import json;d=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/k1check/K1R0_CHECK.json'));print({k:(list(v) if isinstance(v,dict) else v) for k,v in d.items() if k!='authorities'}); print({s:(v.get('sha256'),v.get('counts'),v.get('hits')) for s,v in d['slices'].items()})"
echo ==== sb_alias2; ls /scratch/jjyeung/orch_n30/sb_alias2/out | head; grep -n "210b2534\|sha256" /scratch/jjyeung/orch_n30/sb_alias2/out/ROOM_AUDIT_REPORT.md | head -20
