export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; J=173368
sacct -j $J -n -X -o JobID,State,Elapsed,ExitCode | head -2
grep -v "_cgroup_procs_check\|unable to read" $X/j/a15_cot_ap24a9e61c_$J.err | tail -c 1500
ls -la $X/o/$J; tail -c 1500 $X/o/$J/q.log 2>/dev/null
