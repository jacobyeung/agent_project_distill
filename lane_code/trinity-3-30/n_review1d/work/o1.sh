cd /project/community/jjyeung/okh7/x_22c714e1/o/173626 || exit 1
date -u +%TZ; ls -la . live rd0 2>/dev/null | head -60
echo "@@@ steps"; tail -25 q.steps 2>/dev/null
ls -la /project/community/jjyeung/okh7/x_22c714e1/j/ | tail -8
L=$(ls -t /project/community/jjyeung/okh7/x_22c714e1/j/*173626*.log 2>/dev/null | head -1); echo "LOG $L"; tail -30 "$L"
for f in rdiff_summary.json rd0/rdiff_summary.json db_bytes.json; do [ -f $f ] && { echo "@@@ $f $(sha256sum < $f|cut -c1-64)"; cat $f; echo; }; done
ls -la /project/community/jjyeung/okh7/x_22c714e1/ | head -40
