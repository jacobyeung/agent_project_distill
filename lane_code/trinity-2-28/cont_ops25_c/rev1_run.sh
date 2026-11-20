cd /home/jjyeung/agent_project_distill || exit 1
G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
CR=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs
agent/scripts/codex_dispatch.sh review $G $G/BRIEF_REV1.md --model gpt-6-astra --effort high --label c25_rev1 --skip-git-check
d=$(ls -d $CR/*_c25_rev1 | tail -1)
if [ ! -s "$d/final_message.md" ] && tail -c 20000 "$d/transcript.log" | grep -q 'at capacity'; then
  agent/scripts/codex_dispatch.sh review $G $G/BRIEF_REV1.md --label c25_rev1b --skip-git-check
fi
echo "REV1_DONE $(date -u +%FT%TZ)"
