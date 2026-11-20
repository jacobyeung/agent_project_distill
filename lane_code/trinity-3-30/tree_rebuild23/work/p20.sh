tmux ls | grep tr2; W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z4/out; date -u +%TZ; P=$(ls $Z/tree_rebuild_b24m4z4_*.tar | head -1); test -f $P.sha256 || { echo NO_SHA; exit 0; }; cat $P.sha256; sha256sum $P | cut -c1-16
cat $Z/BUILD24M4Z4_REPORT.md; echo ===MD; cat $Z/ENOSPC_24M4Z4.md; echo ===UL; cat $Z/UPLOADS_24M4Z4*.list; ls $Z | tr '\n' ' '
C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; d=$(ls -d $C/*_tree_rebuild24m4z4 | tail -1); echo $d; head -c 1500 $d/final_message.md
timeout 120 bash -c "cat $P | ssh -o ConnectTimeout=20 trinity-2-28.ib 'cat > /scratch/jjyeung/n30_mirror/tree_rebuild23/$(basename $P) && sha256sum /scratch/jjyeung/n30_mirror/tree_rebuild23/$(basename $P) | cut -c1-16'" < /dev/null
