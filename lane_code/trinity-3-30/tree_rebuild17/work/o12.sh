export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/173555
cat $O/r.log; echo; cat $O/q1.json; echo; cat $O/r1.json; echo; tail -8 $O/q.steps | cut -c1-250; ls -la $O/live; tail -25 $X/j/a15_cot_ap24d9b8e2_173555.log | cut -c1-300; cat $X/j/a15_cot_ap24d9b8e2_173555.err | tail -20 | cut -c1-300
sacct -j 173555 -X -o JobID,State,ExitCode,Start,End,Elapsed -n
