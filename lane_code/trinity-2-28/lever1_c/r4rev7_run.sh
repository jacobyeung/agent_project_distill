B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
while [ -n "l2_r4fix5" ] && tmux has-session -t l2_r4fix5 2>/dev/null; do sleep 30; done
echo "START $(date -u +%FT%TZ)"
mkdir -p $C/r4rev7
bash $B/tools/codex_local.sh review $C/r4rev7 $C/BRIEF_R4REV7.md --model gpt-6-astra --effort high --label lever2_r4rev7 --skip-git-check --writable-root $C/r4rev7 
echo "r4rev7 DONE rc=$? $(date -u +%FT%TZ)"
