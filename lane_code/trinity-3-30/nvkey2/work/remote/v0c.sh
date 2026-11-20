F=/scratch/jjyeung/orch_n30/fb_pack
cat $F/k1point/AUDIT_POINTING_K1.json; echo
cat $F/point/out/REPORT.md | cut -c1-900 | head -50
cat $F/point/STATUS.md
grep -n -E 'admit|18,116|18116|manifest' $F/k1point/audit_point.py $F/k1point/mk_room_removal.py | cut -c1-250 | head -20
