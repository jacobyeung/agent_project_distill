X=/project/community/jjyeung/okh7/x_22c714e1; date -u +%TZ
cd $X/o/173660 && ls -la . keep 2>/dev/null | head -30
for f in db_bytes.json receipt.json import_probe.json timings.json; do [ -f $f ] && { echo "@@@ $f $(sha256sum < $f|cut -c1-64) $(stat -c %s $f)"; head -c 2500 $f; echo; }; done
sha256sum $X/jd5.sh $X/dbb3.py $X/rdiff.py $X/jn.sh 2>&1
cd $X/o/173661 && ls -la . live rd0 2>/dev/null | head -40; tail -3 q.steps 2>/dev/null
