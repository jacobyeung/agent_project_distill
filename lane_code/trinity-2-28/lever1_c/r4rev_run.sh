B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
echo "START $(date -u +%FT%TZ)"
bash $B/tools/codex_local.sh review $C/r4rev $C/BRIEF_R4REV.md --model gpt-6-astra --effort high --label lever1_r4rev --skip-git-check --writable-root $C/r4rev
echo "r4rev DONE rc=$? $(date -u +%FT%TZ)"
