cd /project/community/jjyeung/okh7/x_22c714e1/o/173626 || exit 1
date -u +%TZ; ls -la . live rd0 2>/dev/null | grep -v '^total' | head -60
tail -c 1200 r.log; echo; tail -3 q.steps
ls -la ../../jn.sh 2>&1; sha256sum ../../jn.sh 2>&1
for f in rd0/rdiff_summary.json db_bytes.json a6.json rdiff.log; do [ -f $f ] && { echo "@@@ $f $(sha256sum < $f|cut -c1-64)"; head -c 8000 $f; echo; }; done
