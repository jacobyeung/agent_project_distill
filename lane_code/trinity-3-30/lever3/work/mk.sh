# usage: source mk.sh; mk NAME MODE BRIEF_LOCAL_PATH WAIT_SESSION "extra writable-root flags" >> remote script
mk() { local n=$1 mode=$2 bf=$3 w=$4 extra=$5; local BN=BRIEF_$(echo $n | tr a-z A-Z).md
echo "base64 -d > \$C/$BN <<'B64'"; base64 < $bf; echo "B64"
echo "cat > \$C/${n}_run.sh <<'RUN'"
echo 'B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; C=/scratch/jjyeung/orch_n30/lever1_c'
echo "while [ -n \"$w\" ] && tmux has-session -t $w 2>/dev/null; do sleep 30; done"
echo 'echo "START $(date -u +%FT%TZ)"'
if [ $mode = review ]; then echo "mkdir -p \$C/$n; bash \$B/tools/codex_local.sh review \$C/$n \$C/$BN --model gpt-6-astra --effort high --label lever3_$n --skip-git-check --writable-root \$C/$n"
else echo "bash \$B/tools/codex_local.sh implement \$C/$extra \$C/$BN --model gpt-6-astra --effort high --label lever3_$n --skip-git-check --writable-root \$C/$extra"; fi
echo "echo \"$n DONE rc=\$? \$(date -u +%FT%TZ)\""
echo "RUN"
echo "tmux new-session -d -s l3_$n \"bash \$C/${n}_run.sh > \$C/${n}_run.log 2>&1\""; }
