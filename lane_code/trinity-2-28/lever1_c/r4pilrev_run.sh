B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
while [ -n "l3_r4pil" ] && tmux has-session -t "=l3_r4pil" 2>/dev/null; do sleep 30; done
echo "START $(date -u +%FT%TZ)"
mkdir -p $C/r4pilrev; bash $B/tools/codex_local.sh review $C/r4pilrev $C/BRIEF_R4PILREV.md --model gpt-6-astra --effort high --label lever3_r4pilrev --skip-git-check --writable-root $C/r4pilrev
echo "r4pilrev DONE rc=$? $(date -u +%FT%TZ)"
