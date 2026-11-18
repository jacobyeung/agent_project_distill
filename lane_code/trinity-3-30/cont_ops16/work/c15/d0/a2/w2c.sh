export TZ=UTC; KH=/project/community/jjyeung/okh7/x_8417c021; J=170109
date -u +%FT%TZ; squeue -j $J -o '%i %T %M %N' 2>&1 | tail -1; squeue -j 170111 -o '%i %T %S' 2>&1 | tail -1
cat $KH/o/$J.a.steps 2>&1 | tail -4; cat $KH/o/$J.s2.steps 2>&1 | tail -8
for r in 0 1 2 3; do echo "== r$r"; tail -c 300 $KH/o/$J.s2.r$r.log 2>/dev/null | tr -c '[:print:]\n' ' ' | tail -3; done
ls $KH/runs/fdca77e7/inputs/first_batch_progress/ 2>/dev/null | head
ls -la $KH/o/ 2>&1 | grep "$J\.s2" 
echo "== B"; KB=/project/community/jjyeung/okh7/x_f5c353f7; tail -6 $KB/o/170111.w.steps 2>&1; tail -c 400 $KB/o/170111.err 2>/dev/null | tr -c '[:print:]\n' ' ' | tail -3; ls $KB/o/ 2>/dev/null | grep 170111 | head; ls $KB/runs/359fcc3c 2>/dev/null | head
