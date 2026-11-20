X=/project/community/jjyeung/okh7/x_22c714e1
for f in $X/a24m2/over_n/k/p.json $X/n/k/p.json $X/qd/k/p.json $X/a24m1/over_n/k/p.json $X/a24k/over_n/k/p.json; do test -f $f && python3 -c "
import json;d=json.load(open('$f'));print('$f',d.get('local_map'),len(d.get('link_checks',[])),sorted(d)[:40])"; done
grep -n "k/0.json" $X/o/173368/q.log 2>/dev/null | head; ls $X/o/173368/ 2>/dev/null; tail -c 1500 $X/o/173368/q.log 2>/dev/null
