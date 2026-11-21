B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
while [ -n "l3_r1vpy" ] && tmux has-session -t "=l3_r1vpy" 2>/dev/null; do sleep 30; done
echo "START $(date -u +%FT%TZ)"
mkdir -p $C/r1vpyrev; bash $B/tools/codex_local.sh review $C/r1vpyrev $C/BRIEF_R1VPYREV.md --model gpt-6-astra --effort high --label lever3_r1vpyrev --skip-git-check --writable-root $C/r1vpyrev
echo "r1vpyrev DONE rc=$? $(date -u +%FT%TZ)"
