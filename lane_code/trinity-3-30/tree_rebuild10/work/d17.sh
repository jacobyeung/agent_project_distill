W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W && tar xzf - -C $W && ls -la prompts/build17.md
mkdir -p $W/w17 && cd $W/w17 && tar xf $W/w16b/out/tree_rebuild_b16_04e21e92.tar && du -sh $W/w17 $W
free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1; tmux ls | grep tr10
tmux new -d -s tr10_b17 "cd /home/jjyeung/agent_project_distill && agent/scripts/codex_dispatch.sh implement $W/w17 $W/prompts/build17.md --model gpt-6-astra --effort high --label tree_rebuild17 --skip-git-check > $W/work/build17_dispatch.log 2>&1"
cd $W/w16b && tar czf $W/mirror/tr10_b16_core_04e21e92.tgz work/tree_r1 out/BUILD16_REPORT.md out/TREE_SEAL.json out/TREE_FILES.sha256 work/build16/inputs work/build16/kits/r1 work/build16/KIT_RESULT.json work/build16/DELIVERY.json work/build16/proofs/operator work/build16/proofs/census/CENSUS.json work/build16/proofs/census/PLAN_RUN.json work/build16/proofs/traces/INDEX.json && cd $W && tar cf mirror/tr10_scripts_b16.tar prompts work/conf16/cf16.sh work/conf16/rtr.py work/k1check inputs/rooms && ls -la mirror; sha256sum mirror/tr10_b16_core_04e21e92.tgz mirror/tr10_scripts_b16.tar
sleep 10; tmux ls | grep tr10
