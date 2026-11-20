W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z2/out; date -u +%TZ; P=$Z/tree_rebuild_b24m4z2_baec1ca4.tar; cat $P.sha256; sha256sum $P | cut -c1-16
cat $Z/BUILD24M4Z2_REPORT.md; echo ===MD; cat $Z/ENOSPC_24M4Z2.md; echo ===USAGE; cat $Z/e2/E2_USAGE.md; echo ===E2SH; cat $Z/e2/e2.sh; echo ===RUN; cat $Z/e2/run.sh; echo ===UL; cat $Z/UPLOADS_24M4Z2*.list; ls $Z | tr '\n' ' '
C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; d=$(ls -d $C/*_tree_rebuild24m4z2 | tail -1); echo $d; head -c 1500 $d/final_message.md
timeout 120 bash -c "cat $P | ssh -o ConnectTimeout=20 trinity-2-28.ib 'cat > /scratch/jjyeung/n30_mirror/tree_rebuild23/$(basename $P) && sha256sum /scratch/jjyeung/n30_mirror/tree_rebuild23/$(basename $P) | cut -c1-16'" < /dev/null
