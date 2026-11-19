export TZ=UTC; date -u +%FT%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -h -o "%i %j %P %T %M %R %N"
ls -la $X $X/j $X/o $X/q $X/n 2>&1 | head -120
for J in 173236 173222 173076; do echo "==== $J.out"; test -f $X/j/$J.out && grep -v "_cgroup_procs_check\|unable to read" $X/j/$J.out | cut -c1-400 | tail -120; done
echo "==== q/job.sh"; cat $X/q/job.sh | head -150
echo "==== o/173236"; ls -la $X/o/173236; tar tzvf $X/o/173236/o.tar 2>&1 | head -40
df -h /project/community 2>&1 | tail -2
