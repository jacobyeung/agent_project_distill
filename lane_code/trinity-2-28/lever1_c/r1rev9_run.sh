B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c
while [ -n "l2_r1fix7" ] && tmux has-session -t l2_r1fix7 2>/dev/null; do sleep 30; done
echo "START $(date -u +%FT%TZ)"
mkdir -p $C/r1rev9
bash $B/tools/codex_local.sh review $C/r1rev9 $C/BRIEF_R1REV9.md --model gpt-6-astra --effort high --label lever2_r1rev9 --skip-git-check --writable-root $C/r1rev9 
echo "r1rev9 DONE rc=$? $(date -u +%FT%TZ)"
