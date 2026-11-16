<!-- recovered by seal_plan: transcript=71f94277 line=6104 utc=2026-11-11T19:31:57.799Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; mkdir -p miss_visibility/events miss_visibility/work miss_visibility/out; T=$(date -u +%Y%m%dT%H%MZ)
cat > leg_s1_tree/inbox/${T}_ORCH_j4_rule.md <<'EOF'
# ORCH: the rule for labelling job 4's list (hand read: /scratch/jjyeung/orch_cd/label_247/out/j4/HAND_READ_50.md)
A reader judged 50 agreed rejects with their images: identity rejects are bad rows in 8 of 10 (none fine), absent 5 of 8, merged and combinations mostly bad or poor; extent-only rejects are fine in 8 of 22 and poor in 11, and the poor ones are under-coverage (slivers, scattered fragments, one-pixel lines), not bleed.
Apply to the training-set builder:
1. REMOVE the agreed rejects of job 4 whose defect names identity, absent or merged, alone or in any combination (7,012 rows by the counts in the job's RESULT; print the number you remove).
2. KEEP the extent-only agreed rejects (7,940), but filter targets by shape for ALL grounding rows, not only these: drop a target whose mask area is below the v3.14 pixel floor (min_mask_px, scaled as the runtime scales it) or whose largest connected component holds less than 60% of the mask's pixels. Report how many rows this drops per source and how many of the 7,940 it catches.
3. Keep job 4's unsure and disagree rows; count them in the data-mix table.
A Codex lane (miss_visibility) is building a depth-visibility check for these rows, since most bad ones are ground truth projected onto a hidden object; if its RESULT lands before your receipt is final, take its drop list too.
EOF
cat > miss_visibility/BRIEF.md <<'EOF'
# miss_visibility (Codex Astra): a programmatic visibility check for grounding training rows whose target is projected ground truth, on CPU
Your folder: /scratch/jjyeung/orch_cd/miss_visibility (write only here). Everything else is read-only.

## Why
The student's grounding head trains on rows (frames, object name, target mask or point). 41,140 of them are "MISS" rows: the pipeline's own grounding had missed the object, so the target was made by projecting the scene's ground truth into the frame. Two frontier models rejected 36% of these rows, and a hand read of 50 rejects with images found that most truly bad rows are ground truth projected onto an object that is hidden in that frame (/scratch/jjyeung/orch_cd/label_247/out/j4/HAND_READ_50.md; the job's result: /scratch/jjyeung/orch_cd/label_247/events/20261111T1924Z_RESULT_j4_verdicts.md; a saved note describes the same defect class: /home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/gt-visibility-vertex-splat-defect-20261014.md, one named file you may open). A model's opinion is a slow and biased filter; a depth test is exact. Grounding quality is now the binding lever of the project, so the training targets must be right.

## Inputs
- The rows and their verdicts: /scratch/jjyeung/orch_cd/label_247 (BRIEF.md and STATUS.md explain rows, units and where job 4's rows were built from; out/j4/VERDICTS.jsonl, REMOVE.jsonl, SUMMARY.json; the builder scripts in work/).
- Ground truth with depth on this node: lane dose_pool's per-scene GT.npz files (/scratch/jjyeung/orch_cd/dose_pool/STATUS.md names them: out/t0_gt or similar for 343 scenes, out/t1_gt/gt for 634 scenes, out/arkit_gt for 1,480 ARKit captures; each holds per-frame depth, instance rasters and poses in the format its work/v314 code reads), and toolprog's rasters for ScanNet validation scenes (/scratch/jjyeung/orch_cd/toolprog/work/gt). List one level at a time. Do not pull anything from /data*.

## Build
1. A check that, for a row's frame and target, decides VISIBLE, PARTLY (state the fraction) or HIDDEN from geometry alone: the target's pixels compared with the rendered or sensor depth of the scene at those pixels (is the named object the front surface there, within a tolerance you state and justify), using the instance raster where one exists. No model, no learned threshold beyond the tolerance.
2. Coverage: for how many of the 41,140 rows does ground truth with depth exist on this node (by dataset)? Run the check on all of those.
3. Validation against what we have: the 60 hand-read rows (ids and verdicts in HAND_READ_50.md: does HIDDEN catch the rows judged BAD for identity or absence, and does it spare the ones judged FINE?), and the two models' verdicts (the confusion table of your HIDDEN against their agreed-reject by defect class, and against agreed-accept).
4. The drop list: rows your check marks HIDDEN, and rows PARTLY below a fraction you choose on the hand-read rows only; a JSONL with row id, verdict, fraction, and the evidence numbers; counts by dataset and by the models' status (so we see how many bad rows the models missed).
5. The same check as a function the row builder can call for every projected-ground-truth target in future builds, with tests (a synthetic occluder; a real row of each verdict).

## Deliver
out/MISS_VISIBILITY.md (the rule, coverage, the two validation tables, counts, what it cannot judge), out/DROP_HIDDEN.jsonl, out/visibility.py with tests, events/<UTC stamp from date -u +%Y%m%dT%H%MZ>_RESULT_miss_visibility.md and a final message, each at most 15 lines.

## Limits
CPU only; no GPU, no ssh, no git commands, no network, no deletion commands of any kind, no calls to any model API. Run under `ulimit -f 204800`; folder under 2 GB; temporary files under work/tmp; at most 8 CPU threads. /home and /data* are overloaded network storage: apart from the one named note, do not read or write them. You cannot ask questions: decide, and write the choice down.
EOF
tmux new -d -s cx_miss_visibility "bash /scratch/jjyeung/orch_cd/orch_tools/codex_local.sh implement /scratch/jjyeung/orch_cd/miss_visibility /scratch/jjyeung/orch_cd/miss_visibility/BRIEF.md --model gpt-6-astra --effort high --skip-git-check --label miss_visibility > /scratch/jjyeung/orch_cd/miss_visibility/dispatch.out 2>&1"
S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad; printf 'miss_visibility|tmux:cx_miss_visibility||\n' >> $S/LANES
echo "$(date -u +%Y-%m-%dT%H:%MZ) dose_pool RESULT 1930Z T1 half 1: 634 scenes (9.49 GB pull), GT.npz 634/634 (4.94 GB), rows gen_r2 14,777 (abs 2,986; rel 5,574; medium 3,878; hard 2,339) + gaps 7,862 + room 211; all validators pass; content = released 100%; POOL_S1 now 87,197 rows; half 2 (243 scenes, 9.42 GB) started at 132 GB free; out/T1_REMOVABLE.md lists 634 mesh files (9.39 GB) for the user. HAND READ of job 4 (Claude Opus high, 50 rejects + 10 accepts with images, ScanNet++ batches only): FINE share of agreed rejects 22% [13,35]; identity 0/10 fine (8 BAD), absent 1/8, merged 1/5, combos 1/5, extent 8/22 fine + 11 POOR (under-coverage slivers/fragments, not bleed; the depth trim fixes 1 of 11). RULED for LEG-S1: remove j4 agreed rejects naming identity, absent or merged (7,012 rows); keep extent-only (7,940) but filter ALL grounding targets by shape (pixel floor; largest component >= 60%); keep unsure/disagree. Dispatched Codex Astra miss_visibility (depth-visibility check for projected-GT targets; drop list; builder function)." >> ORCH_HANDOFF.md; sleep 2; tmux ls | grep -c cx_miss_visibility