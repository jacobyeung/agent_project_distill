cd /home/jjyeung/agent_project_distill || exit 1
G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
CR=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs
W="--writable-root /scratch/jjyeung/orch_n30/cont_ops24_c/cap --writable-root /scratch/jjyeung/orch_n30/cont_ops25_c/cam"
agent/scripts/codex_dispatch.sh implement $G $G/BRIEF_R8.md --model gpt-6-astra --effort high --label c25_r8 --skip-git-check $W
d=$(ls -d $CR/*_c25_r8 | tail -1)
if [ ! -s "$d/final_message.md" ] && tail -c 20000 "$d/transcript.log" | grep -q 'at capacity'; then
  echo "ASTRA_CAPACITY $(date -u +%FT%TZ) -> default implement model"
  agent/scripts/codex_dispatch.sh implement $G $G/BRIEF_R8.md --label c25_r8b --skip-git-check $W
fi
echo "R8_DONE $(date -u +%FT%TZ)"
