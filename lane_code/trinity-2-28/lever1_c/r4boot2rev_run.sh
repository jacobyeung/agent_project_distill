B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
while [ -n "" ] && tmux has-session -t "=" 2>/dev/null; do sleep 30; done
echo "START $(date -u +%FT%TZ)"
mkdir -p $C/r4boot2rev; bash $B/tools/codex_local.sh review $C/r4boot2rev $C/BRIEF_R4BOOT2REV.md --model gpt-6-astra --effort high --label lever3_r4boot2rev --skip-git-check --writable-root $C/r4boot2rev
echo "r4boot2rev DONE rc=$? $(date -u +%FT%TZ)"
