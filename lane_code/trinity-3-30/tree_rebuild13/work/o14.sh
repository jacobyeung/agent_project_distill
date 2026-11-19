export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; J=173222
sacct -j $J -n -o JobID,State,Elapsed,ExitCode | head -6
grep -n "fla overlay on" $X/j/$J.out | tail -1
L=$(grep -n "fla overlay on" $X/j/$J.out | tail -1 | cut -d: -f1); tail -n +$L $X/j/$J.out | grep -v "_cgroup_procs_check\|unable to read" | head -60 | cut -c1-500
ls -la $X/j/ | grep $J
