X=/project/community/jjyeung/okh7/x_22c714e1; J=174085
echo "LOOK $(date -u +%FT%TZ)"; ls -la $X/o/$J $X/o/$J/live $X/o/${J}_live 2>&1 | head -40
for f in $X/o/$J/j2.log $X/o/${J}_live/q.log.tail $X/o/${J}_live/mem.txt; do [ -f $f ] && { echo "== $f"; tail -8 $f | cut -c1-250; }; done
scontrol show job $J | grep -oE 'KillOnInvalidDep=[^ ]*|Requeue=[^ ]*|BatchFlag=[^ ]*|TRES=[^ ]*' | head
