W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tail -5 $W/work/build21g_dispatch.log | cut -c1-300
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild21g | head -1); grep -m2 "at capacity" $d/transcript.log | cut -c1-200
tmux new -d -s tr12_b21g2 "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh implement $W/w21 $W/prompts/build21g.md --model gpt-6-astra --effort high --label tree_rebuild21g2 --skip-git-check > $W/work/build21g2_dispatch.log 2>&1"
sleep 45; tmux ls | grep tr12; d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild21g2 | head -1); stat -c %s $d/transcript.log; grep -c "at capacity" $d/transcript.log
