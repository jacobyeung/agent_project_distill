B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
echo "START $(date -u +%FT%TZ)"
mkdir -p $C/r1rev4
bash $B/tools/codex_local.sh review $C/r1rev4 $C/BRIEF_R1REV4.md --model gpt-6-astra --effort high --label lever2_r1rev4 --skip-git-check --writable-root $C/r1rev4
echo "r1rev4 DONE rc=$? $(date -u +%FT%TZ)"
