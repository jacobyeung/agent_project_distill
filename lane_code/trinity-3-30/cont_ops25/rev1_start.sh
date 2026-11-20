G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
cat > $G/BRIEF_REV1.md <<'BRIEFEOF'
# Review (cont_ops25, read-only): is the T1 S2 table right, and what does it license?

Workspace /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild on trinity-2-28 (read-only; your final message is the review). No ssh, Git, GPU, network, deletion. Python /scratch/jjyeung/envs/p1cpu/bin/python for read-only checks.

A selector decision may rest on REPORT7.md section 4 and cap/score_t1/S2_T1.{md,json}: 27 T1 objects first fail at S2 (target proposal in the pool at IoU > 0.5, but at least half of the selected track's nonempty masks miss IoU > 0.5), split by majority class (another instance 8, empty/other 12, mixed 4, part 1, bleed 2). Code: funnel_round7.py, s2_round7.py, round7_common.py, gpkg/join_capture.py; stage rules in RECORD_GROUNDING_FUNNEL.md and REPORT4.md; camera and binding context in REPORT6-REPORT9 if present.

Check, and report only verified problems with file:line and a reproduction:
1. Stage assignment: does an S2 object truly have a raw target proposal on a frame where the selected track is wrong? Is "selected" the track the reader actually used for the printed gap (not a re-derived one)? Are early-lifting losses, linking (a correct proposal split across tracks) and the selector head separable from the capture, or does S2 mix them?
2. Mask mapping to the 240x320 GT grid (reader resize, portrait handling, ScanNet extent readings): could a mapping error turn a right selection into S2 or "empty/other"? What is the "empty/other" class made of (12 of 27)?
3. GT binding: if the ARKit GT is bound to other frames (round 9), which S2 objects are on ARKit and would move?
4. What the table licenses: is "selection-path loss" the strongest supported claim, or does it support "the selector picks the wrong track" specifically? State the claim the evidence supports.
Verdict line: SOUND / SOUND WITH LIMITS / NOT SOUND, then findings ordered by impact. At most 80 lines.
BRIEFEOF
cat > /scratch/jjyeung/orch_n30/cont_ops25_c/rev1_run.sh <<'RUNEOF'
cd /home/jjyeung/agent_project_distill || exit 1
G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
CR=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs
agent/scripts/codex_dispatch.sh review $G $G/BRIEF_REV1.md --model gpt-6-astra --effort high --label c25_rev1 --skip-git-check
d=$(ls -d $CR/*_c25_rev1 | tail -1)
if [ ! -s "$d/final_message.md" ] && tail -c 20000 "$d/transcript.log" | grep -q 'at capacity'; then
  agent/scripts/codex_dispatch.sh review $G $G/BRIEF_REV1.md --label c25_rev1b --skip-git-check
fi
echo "REV1_DONE $(date -u +%FT%TZ)"
RUNEOF
tmux new-session -d -s c25_rev1 "bash /scratch/jjyeung/orch_n30/cont_ops25_c/rev1_run.sh > /scratch/jjyeung/orch_n30/cont_ops25_c/rev1_run.log 2>&1"
sleep 2; tmux ls | grep c25
