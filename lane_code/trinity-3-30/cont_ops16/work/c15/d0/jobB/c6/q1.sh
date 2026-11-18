export TZ=UTC; KB=/project/community/jjyeung/okh7/x_f5c353f7
date -u +%FT%TZ; ls $KB | head -40
echo "== grep"; grep -n -s 'metrics_\|attempt_\|all_rank_native\|first.step gate\|first_step' $KB/*.sh $KB/*.py 2>/dev/null | head -30
echo "== runs"; find $KB/runs/359fcc3c -maxdepth 2 -newer $KB/runs/359fcc3c/inputs/request.json 2>/dev/null | head -20
echo "== steps tail"; tail -3 $KB/o/170111.steps; tail -3 $KB/o/170111.w.steps
echo "== err"; tail -c 1500 $KB/o/170111.err | tr -c '[:print:]\n' ' ' | tail -8
