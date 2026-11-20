B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
echo "START $(date -u +%FT%TZ)"
mkdir -p $C/r4rev5
bash $B/tools/codex_local.sh review $C/r4rev5 $C/BRIEF_R4REV5.md --model gpt-6-astra --effort high --label lever2_r4rev5 --skip-git-check --writable-root $C/r4rev5
echo "r4rev5 DONE rc=$? $(date -u +%FT%TZ)"
