export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/174198; date -u +%TZ
ls -la $O | head -30; cat $O/HOLD.txt 2>/dev/null | head -20; echo ==TB; tail -c 2500 $O/tb.txt 2>/dev/null; echo; for f in $O/q0.json $O/r0.json; do [ -e $f ] && { echo "== $f"; head -c 1200 $f; echo; }; done
