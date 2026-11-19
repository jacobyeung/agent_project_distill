P=/project/community/jjyeung/okh7/a15_cot_apdc76460c3a164
ls -la $P $P/a | head -40
for f in $P/a/*.json; do echo "-- $f $(stat -c %s $f)"; grep -o '[^"]*\(b83a8a35\|69d2930d\|93ccadab\|t_b8\)[^"]*' $f | sort -u | head -20; done
ls -la /project/community/jjyeung/okh7/x_22c714e1/n/k /project/community/jjyeung/okh7/x_22c714e1/k 2>&1 | head -30
