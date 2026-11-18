export TZ=UTC; KH=/project/community/jjyeung/okh7/x_8417c021; J=170109
date -u +%FT%TZ; squeue -j $J -o '%i %T %M %N' 2>&1 | tail -1; squeue -j 170111 -o '%i %T %S' 2>&1 | tail -1
cat $KH/o/$J.a.steps 2>&1 | tail -4; cat $KH/o/$J.s2.steps 2>&1 | tail -8
for r in 0 1 2 3; do echo "== r$r"; tail -c 300 $KH/o/$J.s2.r$r.log 2>/dev/null | tr -c '[:print:]\n' ' ' | tail -3; done
ls $KH/runs/fdca77e7/inputs/first_batch_progress/ 2>/dev/null | head
sacct -u $USER -S now-10days -X -n -P -o JobID,State,Start,NodeList 2>&1 | tail -8
