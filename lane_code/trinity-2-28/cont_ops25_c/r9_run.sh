cd /home/jjyeung/agent_project_distill || exit 1
G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
CR=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs
W="--writable-root /scratch/jjyeung/orch_n30/cont_ops24_c/cap --writable-root /scratch/jjyeung/orch_n30/cont_ops25_c/cam"
agent/scripts/codex_dispatch.sh implement $G $G/BRIEF_R9.md --model gpt-6-astra --effort high --label c25_r9 --skip-git-check --writable-root /scratch/jjyeung/orch_n30/cont_ops24_c/cap
d=$(ls -d $CR/*_c25_r9 | tail -1)
if [ ! -s "$d/final_message.md" ] && tail -c 20000 "$d/transcript.log" | grep -q 'at capacity'; then
  echo "ASTRA_CAPACITY $(date -u +%FT%TZ) -> default implement model"
  agent/scripts/codex_dispatch.sh implement $G $G/BRIEF_R9.md --label c25_r9b --skip-git-check --writable-root /scratch/jjyeung/orch_n30/cont_ops24_c/cap
fi
echo "R9_DONE $(date -u +%FT%TZ)"
