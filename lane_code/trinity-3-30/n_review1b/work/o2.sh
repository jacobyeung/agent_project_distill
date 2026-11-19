cd /project/community/jjyeung/okh7 || exit 1
d=x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/routing; ls -la $d 2>&1 | head
f=$d/rows.sqlite; [ -f "$f" ] && { stat -c '%s %y' $f; head -c 100 $f | od -An -tx1 | tr -d ' \n'; echo; tail -c +101 $f | sha256sum; sha256sum $f $d/materialization.json; }
ls -la x_22c714e1/o/173368/; tail -c 1500 x_22c714e1/o/173368/q.log; echo; cat x_22c714e1/o/173368/r1.json
