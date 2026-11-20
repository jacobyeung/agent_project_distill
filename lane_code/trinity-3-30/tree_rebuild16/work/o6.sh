export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; J=173496
sacct -j $J -n -X -o JobID,State,Elapsed,ExitCode | head -2
grep -v "_cgroup_procs_check\|unable to read" $X/j/a15_cot_ap24d9b8e2_$J.err | tail -c 1200
tail -c 600 $X/j/a15_cot_ap24d9b8e2_$J.log
ls -la $X/o/$J $X/o/$J/live 2>/dev/null | head -30; tail -c 2000 $X/o/$J/q.log 2>/dev/null; cat $X/o/$J/dbb.log 2>/dev/null | tail -5
