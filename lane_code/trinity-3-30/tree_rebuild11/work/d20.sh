W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W && tar xzf - -C $W && ls -la prompts/build20.md prompts/REVIEW19_VERDICT.md
date -u +%TZ; free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1; du -sh $W/w19 $W; tmux ls | grep -E "tr10|tr11"
S=$(du -sm $W/w19 | cut -f1); if [ "$S" -lt 3000 ]; then cp -a $W/w19 $W/w20; else mkdir -p $W/w20 && cd $W/w20 && tar xf $W/w19/out/tree_rebuild_b19_8ea1fe6b.tar; fi
du -sh $W/w20; ls $W/w20
tmux new -d -s tr11_b20 "cd /home/jjyeung/agent_project_distill && agent/scripts/codex_dispatch.sh implement $W/w20 $W/prompts/build20.md --model gpt-6-astra --effort high --label tree_rebuild20 --skip-git-check > $W/work/build20_dispatch.log 2>&1"
sleep 5; tmux ls | grep tr11
