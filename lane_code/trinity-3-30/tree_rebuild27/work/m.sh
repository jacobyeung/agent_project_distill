# one compact line from the newest watch.log record
W=/scratch/jjyeung/orch_n30/tree_rebuild27/work/watch.log
l=$(grep 'state=' $W | tail -1); q=$(grep '^  q:' $W | tail -1 | md5sum | cut -c1-6); j=$(grep '^  j2:' $W | tail -1 | cut -c1-140)
echo "$l" | awk -v q=$q '{for(i=1;i<=NF;i++) if($i~/^(state|n|anon|file|tmp_freeK|j2|tq|kitlive)=/) s=s" "$i; print $1 s " qh=" q}'; echo "$l" | grep -o 'alarm=\[[^]]*\] gate=\[[^]]*\]' | grep -v 'alarm=\[\] gate=\[v.json absent;WAITING_REVIEW.json absent;review.json absent;gate_copy not yet;\]'
echo "   $j"
