W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W && tar xzf - -C $W && ls -la prompts/build19.md prompts/RULING_0344Z.md
tmux ls | grep tr10
mkdir -p $W/w19 && cd $W/w19 && tar xf $W/w18/out/tree_rebuild_b18_60e6ea72.tar && du -sh $W/w19 $W
free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1
tmux new -d -s tr10_b19 "cd /home/jjyeung/agent_project_distill && agent/scripts/codex_dispatch.sh implement $W/w19 $W/prompts/build19.md --model gpt-6-astra --effort high --label tree_rebuild19 --skip-git-check > $W/work/build19_dispatch.log 2>&1"
sleep 5; tmux ls | grep tr10
