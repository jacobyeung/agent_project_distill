B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
while [ -n "l3_r1wt" ] && tmux has-session -t "=l3_r1wt" 2>/dev/null; do sleep 30; done
echo "START $(date -u +%FT%TZ)"
mkdir -p $C/r1wtrev; bash $B/tools/codex_local.sh review $C/r1wtrev $C/BRIEF_R1WTREV.md --model gpt-6-astra --effort high --label lever3_r1wtrev --skip-git-check --writable-root $C/r1wtrev
echo "r1wtrev DONE rc=$? $(date -u +%FT%TZ)"
