B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
while [ -n "l3_r4clos" ] && tmux has-session -t "=l3_r4clos" 2>/dev/null; do sleep 30; done
echo "START $(date -u +%FT%TZ)"
mkdir -p $C/r4closrev; bash $B/tools/codex_local.sh review $C/r4closrev $C/BRIEF_R4CLOSREV.md --model gpt-6-astra --effort high --label lever3_r4closrev --skip-git-check --writable-root $C/r4closrev
echo "r4closrev DONE rc=$? $(date -u +%FT%TZ)"
