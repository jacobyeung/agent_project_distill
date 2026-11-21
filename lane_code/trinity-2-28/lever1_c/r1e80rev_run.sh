B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
while [ -n "l3_r1e80" ] && tmux has-session -t "=l3_r1e80" 2>/dev/null; do sleep 30; done
echo "START $(date -u +%FT%TZ)"
mkdir -p $C/r1e80rev; bash $B/tools/codex_local.sh review $C/r1e80rev $C/BRIEF_R1E80REV.md --model gpt-6-astra --effort high --label lever3_r1e80rev --skip-git-check --writable-root $C/r1e80rev
echo "r1e80rev DONE rc=$? $(date -u +%FT%TZ)"
