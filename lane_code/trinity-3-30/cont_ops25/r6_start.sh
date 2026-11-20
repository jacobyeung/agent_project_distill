set -u
mkdir -p /scratch/jjyeung/orch_n30/cont_ops25_c
G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
ls -la $G/BRIEF_R6.md $G | head -40
ls -la /scratch/jjyeung/orch_n30/cont_ops24_c/cap | head -40
tmux ls 2>&1
cat > /scratch/jjyeung/orch_n30/cont_ops25_c/r6_run.sh <<'EOF'
cd /home/jjyeung/agent_project_distill || exit 1
G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
CR=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs
agent/scripts/codex_dispatch.sh implement $G $G/BRIEF_R6.md --model gpt-6-astra --effort high --label c25_r6 --skip-git-check --writable-root /scratch/jjyeung/orch_n30/cont_ops24_c/cap
d=$(ls -d $CR/*_c25_r6 | tail -1)
if [ ! -s "$d/final_message.md" ] && tail -c 20000 "$d/transcript.log" | grep -q 'at capacity'; then
  echo "ASTRA_CAPACITY $(date -u +%FT%TZ) -> default implement model"
  agent/scripts/codex_dispatch.sh implement $G $G/BRIEF_R6.md --label c25_r6b --skip-git-check --writable-root /scratch/jjyeung/orch_n30/cont_ops24_c/cap
fi
echo "R6_DONE $(date -u +%FT%TZ)"
EOF
tmux new-session -d -s c25_r6 "bash /scratch/jjyeung/orch_n30/cont_ops25_c/r6_run.sh > /scratch/jjyeung/orch_n30/cont_ops25_c/r6_run.log 2>&1"
sleep 3; tmux ls; nproc; free -g | head -2; df -h /scratch | tail -1
