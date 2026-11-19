X=/project/community/jjyeung/okh7/x_22c714e1; ls $X/o/ 2>/dev/null | tail -5; D=$X/o/173222; ls -la $D; cat $D/RESULT.json; echo
tar tzvf $D/o.tar; echo ====; tar xzOf $D/o.tar q.log | tail -40 | cut -c1-500
echo ==== RESULT; tar xzOf $D/o.tar p/q/RESULT.json 2>/dev/null | head -c 3000
