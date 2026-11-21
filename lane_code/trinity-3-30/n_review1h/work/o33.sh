X=/project/community/jjyeung/okh7/x_22c714e1; TZ=UTC date +%TZ; df -h /project/community < /dev/null | tail -1
sha256sum $X/jn4.sh $X/jn3.sh < /dev/null
echo "== jn4.sh"; cat $X/jn4.sh < /dev/null
echo "== 173991"; ls -la $X/o/173991 < /dev/null; cat $X/o/173991/j2.log < /dev/null; echo "-- err"; cat $X/o/173991/j2.err < /dev/null | head -20
echo "== 173964"; ls -la $X/o/173964 $X/o/173964_x < /dev/null 2>&1 | head -30; tail -c 1200 $X/o/173964/j2.log < /dev/null
