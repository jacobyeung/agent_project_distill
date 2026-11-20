cd /project/community/jjyeung/okh7/x_22c714e1/o/173567 || exit 1
sha256sum r.log q1.json r1.json; tail -c 5000 r.log; echo; grep -a -n -i -E 'direct_schema|schema_fail|blocker|blocked' r.log | cut -c1-400 | tail -20
