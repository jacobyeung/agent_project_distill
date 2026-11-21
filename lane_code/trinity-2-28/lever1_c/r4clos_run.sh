B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
while [ -n "" ] && tmux has-session -t "=" 2>/dev/null; do sleep 30; done
echo "START $(date -u +%FT%TZ)"
bash $B/tools/codex_local.sh implement $C/r4kit $C/BRIEF_R4CLOS.md --model gpt-6-astra --effort high --label lever3_r4clos --skip-git-check --writable-root $C/r4kit
echo "r4clos DONE rc=$? $(date -u +%FT%TZ)"
