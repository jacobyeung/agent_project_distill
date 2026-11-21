B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
while [ -n "" ] && tmux has-session -t  2>/dev/null; do sleep 30; done
echo "START $(date -u +%FT%TZ)"
mkdir -p $C/r1
bash $B/tools/codex_local.sh implement $C/r1 $C/BRIEF_R1FIX9.md --model gpt-6-astra --effort high --label lever2_r1fix9 --skip-git-check --writable-root $C/r1 --writable-root $C/r1_fixtures_old
echo "r1fix9 DONE rc=$? $(date -u +%FT%TZ)"
