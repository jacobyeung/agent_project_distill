W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z/out; date -u +%TZ; cat $Z/*.sha256; sha256sum $Z/tree_rebuild_b24m4z_*.tar | cut -c1-16
cat $Z/BUILD24M4Z_REPORT.md; echo ===MD; wc -c $Z/ENOSPC_24M4Z.md; cat $Z/ENOSPC_24M4Z.md | cut -c1-900
echo ===PATCH; grep -E "^(\+\+\+|---|@@)" $Z/KIT_CHANGE_24M4Z.patch | head -30; echo ===JN2; cat $Z/jn2.sh
C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; d=$(ls -d $C/*_tree_rebuild24m4z | tail -1); echo $d; head -c 1200 $d/final_message.md
