W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
tmux kill-session -t tr10_b16; sleep 5; pgrep -af "tree_rebuild16|w16" | grep -v pgrep | cut -c1-200
cp $W/prompts/build16.md $W/prompts/build16_v1_stopped.md
printf '%s' "$1" | base64 -d > $W/prompts/build16.md; grep -c w16b $W/prompts/build16.md
mkdir -p $W/w16b && cd $W/w16b && tar xf $W/w15/out/tree_rebuild_b15_67f8baf1.tar && du -sh $W/w16b
free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1
tmux new -d -s tr10_b16b "cd /home/jjyeung/agent_project_distill && agent/scripts/codex_dispatch.sh implement $W/w16b $W/prompts/build16.md --model gpt-6-astra --effort high --label tree_rebuild16b --skip-git-check > $W/work/build16b_dispatch.log 2>&1"
sleep 10; tmux ls | grep tr10; tail -c 400 $W/w16/work/build16/STATUS.md
