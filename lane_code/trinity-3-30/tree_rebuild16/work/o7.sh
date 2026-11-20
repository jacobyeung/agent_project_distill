export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; J=173496
sacct -j $J -o JobID,State,Elapsed,ExitCode,Start,End | head -5
grep -v "_cgroup_procs_check\|unable to read" $X/j/a15_cot_ap24d9b8e2_$J.err | grep -v "archive members verified\|staged$" | tail -40 | cut -c1-300
echo ==== LOG; grep -v "archive members verified\|staged$" $X/j/a15_cot_ap24d9b8e2_$J.log | tail -30 | cut -c1-300
cat $X/o/$J/r1.json; echo; grep -n "h/k\|/h/" $X/qd/b/x.py $X/qd/b/a.py $X/qd/job.sh $X/qd/b/q.sh 2>/dev/null | head -20; ls $X/qd/k
