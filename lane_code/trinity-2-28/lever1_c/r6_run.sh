B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
echo "START $(date -u +%FT%TZ)"
bash $B/tools/codex_local.sh implement $C/r6 $C/BRIEF_R6.md --model gpt-6-astra --effort high --label lever1_r6 --skip-git-check --writable-root $C/r6
echo "R6_DONE rc=$? $(date -u +%FT%TZ)"
