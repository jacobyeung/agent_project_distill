export TZ=UTC; KB=/project/community/jjyeung/okh7/x_f5c353f7
date -u +%T; ls -la --time-style=+%T $KB/o/170111.stop $KB/o/170111.err $KB/o/170111.steps; cat $KB/o/170111.stop | head -c 600; echo
tail -c 3000 $KB/o/170111.err | tr -c '[:print:]\n' ' ' | grep -v -i 'FutureWarning\|set_state_dict_type\|^ *$' | tail -8
tail -c 300000 $KB/runs/359fcc3c/metrics_170111.jsonl | tail -1 | head -c 200; echo
