W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; R=$W/w21/out/BUILD21_REPORT.md; B=$W/w21/work/build21
free -g | sed -n 2p; tmux ls
tmux new -d -s tr12_rev21 "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh review $W/w21 $W/prompts/review21.md --model gpt-6-astra --effort high --label tree_rebuild_rev21 --skip-git-check > $W/work/review21_dispatch.log 2>&1"
cat $B/focused.py | cut -c1-600; echo; cat $B/run.sh 2>/dev/null | head -20
sed -n '23298,23380p' $R | cut -c1-700
