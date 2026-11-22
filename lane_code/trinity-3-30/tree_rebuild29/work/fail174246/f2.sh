export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/174246
echo "== tb"; cat $O/tb.txt; echo; echo "== RESULT"; cat $O/RESULT.json; echo; echo "== a6"; cat $O/a6.json | cut -c1-1200; echo; echo "== r1"; cat $O/r1.json | cut -c1-900; echo
echo "== otar"; tar tzf $O/o.tar 2>/dev/null | head -60 || tar tf $O/o.tar | head -60
echo "== B64"; base64 -w0 $O/o.tar; echo
