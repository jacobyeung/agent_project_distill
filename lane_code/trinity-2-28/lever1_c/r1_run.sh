B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
C=/scratch/jjyeung/orch_n30/lever1_c
echo "START $(date -u +%FT%TZ)"
bash $B/tools/codex_local.sh implement $C/r1 $C/BRIEF_R1.md --model gpt-6-astra --effort high --label lever1_r1 --skip-git-check --writable-root $C/r1
echo "R1_DONE rc=$? $(date -u +%FT%TZ)"
