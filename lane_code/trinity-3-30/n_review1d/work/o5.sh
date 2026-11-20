cd /project/community/jjyeung/okh7/x_22c714e1/o/173626 || exit 1
date -u +%TZ; cat r1.json; echo; cat dbb.log; echo; cat b4r.json; echo; cat k_dr_p_q_base_refresh_r.json; echo
grep -n -i "error\|Traceback\|refus\|raise\|Exception\|R1_\|P_TRAINED" r.log | cut -c1-600 | tail -30
echo "@@@ q1 head"; head -c 3000 q1.json; echo
tail -c 4000 /project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap24d9b8e2_173626.log
grep -v cgroup /project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap24d9b8e2_173626.err | tail -30 | cut -c1-600
