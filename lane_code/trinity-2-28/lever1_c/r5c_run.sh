B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
echo "START $(date -u +%FT%TZ)"
mkdir -p $C/nogt
bash $B/tools/codex_local.sh implement $C/nogt $C/BRIEF_R5C.md --model gpt-6-astra --effort high --label lever2_r5c --skip-git-check --writable-root $C/nogt
echo "r5c DONE rc=$? $(date -u +%FT%TZ)"
