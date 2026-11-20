B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
echo "START $(date -u +%FT%TZ)"
bash $B/tools/codex_local.sh review $C/r4rev2 $C/BRIEF_R4REV2.md --model gpt-6-astra --effort high --label lever2_r4rev2 --skip-git-check --writable-root $C/r4rev2
echo "r4rev2 DONE rc=$? $(date -u +%FT%TZ)"
