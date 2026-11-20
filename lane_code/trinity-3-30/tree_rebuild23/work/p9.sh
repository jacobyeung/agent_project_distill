W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z/out; date -u +%TZ; P=$Z/tree_rebuild_b24m4z_a202d1ec.tar
timeout 120 bash -c "cat $P | ssh -o ConnectTimeout=20 trinity-2-28.ib 'cat > /scratch/jjyeung/n30_mirror/tree_rebuild23/$(basename $P) && sha256sum /scratch/jjyeung/n30_mirror/tree_rebuild23/$(basename $P) | cut -c1-16'" < /dev/null
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild/enospc24m4z; mkdir -p $E && cp $Z/ENOSPC_24M4Z.md $Z/ENOSPC_24M4Z.json $Z/jn2.sh $Z/KIT_CHANGE_24M4Z.patch $Z/BUILD24M4Z_REPORT.md $E/ && sha256sum $E/* | cut -c1-90
grep -n "x.py\|print\|stdout" $W/w24z/work/enospc/decoded_j.sh | head -20 | cut -c1-250
