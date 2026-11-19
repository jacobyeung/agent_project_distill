export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; J=173076
sacct -j $J -n -o JobID,State,Elapsed,ExitCode,MaxRSS | head -5
grep -v "_cgroup_procs_check\|unable to read\|joined\|members verified\|staged$" $X/j/$J.out | tail -40 | cut -c1-400
echo ==== g.py; cat $X/q/b/g.py | head -30
echo ====; grep -n "g.py\|E42" $X/q/job.sh $X/q/b/*.sh 2>/dev/null | head -20 | cut -c1-300
