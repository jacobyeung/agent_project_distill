W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr12; ls $W/w21/out | grep -E 'b21d|21D'
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild21d | head -1); stat -c '%s %y' $d/transcript.log; grep -c "at capacity" $d/transcript.log; ls $d | tr '\n' ' '; tail -c 1500 $d/transcript.log | tr -cd '[:print:]\n' | grep -v '^[ +-@]' | tail -4
grep -n 'Error\|FAIL' $W/work/conf21c/pkg/work/build21/final_focused.log | head -5; tail -3 $W/work/conf21c/pkg/work/build21/final_focused.log
ls /scratch/jjyeung/io_governor/ | tr '\n' ' '
