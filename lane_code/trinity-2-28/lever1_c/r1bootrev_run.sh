B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
while [ -n "l2_r1boot" ] && tmux has-session -t l2_r1boot 2>/dev/null; do sleep 30; done
echo "START $(date -u +%FT%TZ)"
mkdir -p $C/r1bootrev
bash $B/tools/codex_local.sh review $C/r1bootrev $C/BRIEF_R1BOOTREV.md --model gpt-6-astra --effort high --label lever2_r1bootrev --skip-git-check --writable-root $C/r1bootrev 
echo "r1bootrev DONE rc=$? $(date -u +%FT%TZ)"
