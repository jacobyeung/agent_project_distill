export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; J=173368
squeue -j $J -h -o "%i %P %T %M %R %N" 2>/dev/null; sacct -j $J -n -X -o JobID,State,Elapsed,ExitCode 2>/dev/null | head -2
for f in $X/j/a15_cot_ap24a9e61c_$J.log $X/j/a15_cot_ap24a9e61c_$J.err; do test -f $f && { echo "== $f $(stat -c %s $f)"; grep -v "_cgroup_procs_check\|unable to read" $f | tail -c 1500; }; done
ls -la $X/o/$J 2>/dev/null
