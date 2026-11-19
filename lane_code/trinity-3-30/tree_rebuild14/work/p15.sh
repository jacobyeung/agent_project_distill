W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls 2>&1 | grep -E "tr1[34]"; free -g | sed -n 2p
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild24e | head -1); ls $d | tr '\n' ' '; echo; test -f $d/final_message.md && head -c 3000 $d/final_message.md || tail -c 1500 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -5 | cut -c1-300
sed -n 195,215p /tmp/tr14_j.sh </dev/null | cut -c1-220
grep -n "init" /tmp/tr14_j.sh </dev/null | grep -i -E "tk_current|hp |part|gs|loc" | head -10 | cut -c1-220
