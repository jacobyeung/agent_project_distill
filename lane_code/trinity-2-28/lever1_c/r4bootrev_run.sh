B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
while [ -n "l2_r4boot" ] && tmux has-session -t l2_r4boot 2>/dev/null; do sleep 30; done
echo "START $(date -u +%FT%TZ)"
mkdir -p $C/r4bootrev
bash $B/tools/codex_local.sh review $C/r4bootrev $C/BRIEF_R4BOOTREV.md --model gpt-6-astra --effort high --label lever2_r4bootrev --skip-git-check --writable-root $C/r4bootrev 
echo "r4bootrev DONE rc=$? $(date -u +%FT%TZ)"
