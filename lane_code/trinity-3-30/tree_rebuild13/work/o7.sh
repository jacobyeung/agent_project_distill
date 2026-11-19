export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1
scontrol show node orchard-community-2 | grep -i "gres\|AvailableFeatures\|Partitions" | head -5
sinfo -N -p preempt -h -o "%N %G %f %T" | sort -u | head -40
sacct -j 173076 -n -X -o NodeList,AllocTRES%80
grep -rn "g\.py" $X/q/job.sh $X/q/b/ 2>/dev/null | head -8 | cut -c1-250
scontrol show partition preempt | head -20
