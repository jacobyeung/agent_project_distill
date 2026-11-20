B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
echo "START $(date -u +%FT%TZ)"
bash $B/tools/codex_local.sh implement $C/r4kit $C/BRIEF_R4FIX.md --model gpt-6-astra --effort high --label lever2_r4fix --skip-git-check --writable-root $C/r4kit
echo "l2r4fix DONE rc=$? $(date -u +%FT%TZ)"
