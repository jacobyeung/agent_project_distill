export TZ=UTC; KB=/project/community/jjyeung/okh7/x_f5c353f7; R=$KB/runs/359fcc3c
date -u +%FT%TZ; squeue -j 170111 -h -o '%i %T %M %N' 2>&1
ls -la $R | grep -v '^d'
echo "== steps"; tail -4 $KB/o/170111.steps; tail -2 $KB/o/170111.w.steps
echo "== err"; tail -c 3000 $KB/o/170111.err | tr -c '[:print:]\n' ' ' | grep -v -i 'FutureWarning\|set_state_dict_type\|^ *$' | tail -6
echo "== gate"; grep -s -h -i 'gate\|native\|refus' $KB/o/170111.steps $KB/o/170111.err | tail -6
echo "== METRICS_BEGIN"; head -c 3000000 $R/metrics_170111.jsonl 2>/dev/null | head -5; echo "== METRICS_END"
echo "== ATTEMPT_BEGIN"; cat $R/attempt_170111.json 2>/dev/null; echo; echo "== ATTEMPT_END"
echo "== sstat"; sstat -j 170111.batch -n -o AveCPU,MaxRSS 2>&1 | head -2; date -u +%FT%TZ; ls -la --time-style=full-iso $R/metrics_170111.jsonl $KB/o/170111.err
