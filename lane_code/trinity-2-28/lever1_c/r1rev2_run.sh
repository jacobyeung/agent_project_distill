B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
echo "START $(date -u +%FT%TZ)"
bash $B/tools/codex_local.sh review $C/r1rev2 $C/BRIEF_R1REV2.md --model gpt-6-astra --effort high --label lever1_r1rev2 --skip-git-check --writable-root $C/r1rev2
echo "R1REV2_DONE rc=$? $(date -u +%FT%TZ)"
