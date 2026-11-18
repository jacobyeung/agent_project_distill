export TZ=UTC; KA=/project/community/jjyeung/okh7/x_8417c021; KB=/project/community/jjyeung/okh7/x_f5c353f7
date -u +%FT%TZ; squeue -j 170109,170111 -h -o '%i %T %M %N' 2>&1
echo "== A2"; tail -5 $KA/o/170109.s2.steps 2>&1; ls -la $KA/o/ 2>/dev/null | grep '170109\.s2\.\(json\|final\)'
echo "== B w.steps"; tail -8 $KB/o/170111.w.steps 2>&1
echo "== B steps"; tail -12 $KB/o/170111.steps 2>&1
echo "== B err"; tail -c 600 $KB/o/170111.err 2>/dev/null | tr -c '[:print:]\n' ' ' | tail -4
echo "== B o"; ls -la $KB/o/ 2>/dev/null | grep 170111
echo "== B runs"; ls -la $KB/runs/ $KB/runs/359fcc3c 2>&1 | head -20
echo "== B sstat"; sstat -j 170111.batch -n -o AveCPU,MaxRSS 2>&1 | head -2
echo "== B inputs"; ls -la $KB/runs/359fcc3c/inputs/ 2>&1 | tail -6; ls $KB/runs/359fcc3c/inputs/*/ 2>/dev/null | tail -6
