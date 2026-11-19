W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
tmux kill-session -t tr10_b17; sleep 5; pgrep -af "tree_rebuild17" | grep -v pgrep | cut -c1-150
cp $W/prompts/build17.md $W/prompts/build17_v1_stopped.md
cd $W && tar xzf - -C $W && grep -c w17b prompts/build17.md
mkdir -p $W/w17b && cd $W/w17b && tar xf $W/w16b/out/tree_rebuild_b16_04e21e92.tar && du -sh $W/w17b $W
free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1
tmux new -d -s tr10_b17b "cd /home/jjyeung/agent_project_distill && agent/scripts/codex_dispatch.sh implement $W/w17b $W/prompts/build17.md --model gpt-6-astra --effort high --label tree_rebuild17b --skip-git-check > $W/work/build17b_dispatch.log 2>&1"
sleep 10; tmux ls | grep tr10
