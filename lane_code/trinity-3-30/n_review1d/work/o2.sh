cd /project/community/jjyeung/okh7/x_22c714e1/o/173626 || exit 1
date -u +%TZ; ls -la . live rd0 2>/dev/null | head -60
L=/project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap24d9b8e2_173626.log; tail -c 3000 $L; echo; ls -la ${L%.log}.err; tail -c 1500 ${L%.log}.err
for f in rd0/rdiff_summary.json db_bytes.json a6.json r1.json; do [ -f $f ] && { echo "@@@ $f $(sha256sum < $f|cut -c1-64)"; head -c 6000 $f; echo; }; done
