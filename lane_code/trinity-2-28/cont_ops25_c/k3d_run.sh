cd /home/jjyeung/agent_project_distill || exit 1
G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
CR=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs
W="--writable-root /scratch/jjyeung/orch_n30/cont_ops24_c/cap --writable-root /scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres"
agent/scripts/codex_dispatch.sh implement $G $G/BRIEF_K3D.md --model gpt-6-astra --effort high --label c25_k3e --skip-git-check $W
d=$(ls -d $CR/*_c25_k3e | tail -1)
if [ ! -s "$d/final_message.md" ] && tail -c 20000 "$d/transcript.log" | grep -q 'at capacity'; then
  echo "ASTRA_CAPACITY $(date -u +%FT%TZ) -> default implement model"
  agent/scripts/codex_dispatch.sh implement $G $G/BRIEF_K3D.md --label c25_k3eb --skip-git-check $W
fi
echo "K3D_DONE $(date -u +%FT%TZ)"
