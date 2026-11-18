K=/project/community/jjyeung/okh7
ls -laR $K/x_69d2930d/runs/673bc60f/inputs | head -30
ls -la $K | grep -E "b9ef552934627|f40065df28aa3|d72cdcff1e22a|b9188e9225a85"
for d in $K/a15_cot_apb9ef552934627 $K/a15_cot_apf40065df28aa3; do echo "== $d"; ls -la $d 2>&1 | head; done
