cd /project/community/jjyeung/okh7/x_22c714e1/o/173661 || exit 1
date -u +%TZ; cat q1.json; echo; cat r1.json; echo; cat dbb.log
grep -n "Traceback\|Error\|refus" r.log | cut -c1-300 | tail -12
L=$(grep -n "Traceback" r.log | tail -1 | cut -d: -f1); sed -n "$((L-3)),$((L+12))p" r.log | cut -c1-400
tail -3 /project/community/jjyeung/okh7/x_22c714e1/j/*_173661.log
