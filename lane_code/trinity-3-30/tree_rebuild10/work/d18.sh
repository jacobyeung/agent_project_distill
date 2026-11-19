W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W && tar xzf - -C $W && ls -la prompts/build18.md
tmux ls | grep tr10
mkdir -p $W/w18 && cd $W/w18 && tar xf $W/w17b/out/tree_rebuild_b17_846ead7a.tar && du -sh $W/w18 $W
free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1
tmux new -d -s tr10_b18 "cd /home/jjyeung/agent_project_distill && agent/scripts/codex_dispatch.sh implement $W/w18 $W/prompts/build18.md --model gpt-6-astra --effort high --label tree_rebuild18 --skip-git-check > $W/work/build18_dispatch.log 2>&1"
cd $W/w17b && tar czf $W/mirror/tr10_b17_core_846ead7a.tgz work/tree_r1 out/BUILD17_REPORT.md out/EXPORT_RECEIPT_USAGE.md out/TREE_SEAL.json work/build17/inputs work/build17/KIT_RESULT.json work/build17/DELIVERY.json work/build17/proofs/operator work/build17/proofs/rooms/RESULT.json && ls -la $W/mirror/tr10_b17_core_846ead7a.tgz && sha256sum $W/mirror/tr10_b17_core_846ead7a.tgz; cat $W/w17b/work/build17/DELIVERY.json | head -c 400
sleep 5; tmux ls | grep tr10
