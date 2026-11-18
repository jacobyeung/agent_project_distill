<!-- recovered by seal_plan: transcript=a97ad692 line=2985 utc=2026-11-15T08:56:57.898Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd; S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/a97ad692-7041-4f72-8b75-8f8e29df8950/scratchpad; mkdir -p $R/tree_review3/{events,inbox,out,work}
cat > $R/rs_rows/BRIEF3.md <<EOF
# Lane rs_rows, third pass: room-size rows as direct rows; stricter grammar; withheld rooms

Read and obey \`$R/orch_tools/CODEX_BUILD_COMMON_20261115.md\` first (this node's disk is low: check \`df\` before any write over 50 MB; stop below 60 GiB free). Then read your own \`STATUS.md\`, \`out/ROWS_REPORT_R2.md\`, and these three inputs:
- the pre-registration \`/data2/jjyeung/agent_project_data/distill_design/REFREEZE_PREREGISTRATION_20261115.md\` (single file; decision D2): the clean evidence cannot decide whether room size should be answered by a program, so it defaults to DIRECT in the next leg;
- the integration tree's fifth-pass report \`$R/rs_tree/out/TREE_REPORT_R5.md\`, its withheld-room list \`$R/rs_tree/out/WITHHELD_ROOMS_R5.json\` (80 rooms withheld from all training data) and its stricter copy of the grammar validator inside \`$R/rs_tree/work/tree_r1\` (find it from the report);
- the second tree review's low-risk grammar findings in \`$R/tree_review2/out/REVIEW_VERDICT_TREE_R3.md\`.

## Build
1. **Room-size direct rows.** Render the leg's room-size questions (the sealed leg's room program rows and the room items of your unit family) as direct rows in the ruled grammar (\`$R/trace_ruling/out/TRACE_RULING_20261115.md\` section 2.1 and the object-size rendering in 2.2 as the model): Locate lines for what the row's source supplies, Step lines for the question's own logic (which room, which unit), no call, no stated area or length; the estimate appears only as the answer, in the unit the question asks, with the unit conversion done in building the answer and a metric twin for every non-metric question. Exclude the 1,172 rows without lineage and every row of a withheld room. Keep the program rendering of room size as an unadmitted kit under \`out/kits/\`.
2. **One validator.** Make \`work/trace_grammar.py\` the superset of your rules and the tree's stricter copy (glued units, numbers as words including "half a meter" and "a dozen", bare answer restatements such as "So the answer is A." and "Option A is correct.", filler-only traces), with mutation tests, and re-validate every row of \`out/rows_r2\`; report rows refused by the stricter rules per family and re-render those that fail.
3. **Withheld rooms.** Remove from every family the rows of the 80 withheld rooms; report the count per family.
4. Unit family: drop its room-size program rows from the admitted set (room is direct now); keep the distance unit rows as program rows.

## Prove and deliver
Every delivered row passes the superset validator; answers of re-rendered sealed rows are byte-identical to their sources; per-type answer distributions before and after; mutation tests; coverage. Deliver \`out/rows_r3/<family>/\` with manifests (unchanged families may be referenced by manifest hash instead of copied), \`out/SAMPLES_R3.md\` with 12 fixed-seed rows for each new or re-rendered family, \`out/ROWS_REPORT_R3.md\`, RESULT events as the common rules say. No tree is edited.
EOF
setsid nohup bash $R/orch_tools/codex_local.sh implement $R/rs_rows $R/rs_rows/BRIEF3.md --model gpt-6-astra --effort high --label rs_rows3 --skip-git-check < /dev/null > $R/rs_rows/out/codex_stdout_03.log 2>&1 &
cat > $R/tree_review3/BRIEF.md <<EOF
NOTE ON YOUR WORKING DIRECTORY: you were started in /home/jjyeung/agent_project_distill only because Devin requires a trusted workspace. That folder is on overloaded network storage. Do not search, index, list or read it, never use a built-in search or grep tool on /home or /data*, and never run git there. Do all work in the lane folder $R/tree_review3, using absolute paths.

# Lane tree_review3: third independent review of the integration tree for the next training leg (read-only; try to break it)

## What is being reviewed
A GPT-family lane revised \`$R/rs_tree/work/tree_r1\` twice more after the second review (\`$R/tree_review2/out/REVIEW_VERDICT_TREE_R3.md\`, verdict NOT READY; read it whole). Its briefs for those passes are \`$R/rs_tree/BRIEF4.md\` and \`BRIEF5.md\`; reports \`out/TREE_REPORT_R4.md\`, \`out/TREE_REPORT_R5.md\`, \`out/REVIEW_DISPOSITION_R4.md\`, \`out/COMPONENT_POLICY_R5.md\`, \`out/WITHHELD_ROOMS_R5.json\`, \`out/WITHHOLDING_AUDIT_R5.json\`, \`out/CHANGED_LINE_COVERAGE_R5.json\`, \`out/FRAME_HOST_STATEMENTS_R5.json\`, \`out/HOLDER_CPU_JOB_R5.md\`, the pre-launch card \`out/PRELAUNCH_CARD_DRAFT.md\`, the diff and hashes. Rulings it must implement: the trace ruling (\`$R/trace_ruling/out/TRACE_RULING_20261115.md\`), the scene evidence (\`$R/scene_evidence/out/SCENE_EVIDENCE.md\` and \`EVIDENCE_*.json\`), the integrity audit and pre-registration (\`/data2/jjyeung/agent_project_data/distill_design/POLICY_AUDIT_20261115.md\`, \`REFREEZE_PREREGISTRATION_20261115.md\`; single files). The lane still says the strict CPU gate is not met (28 unexecuted changed statements: 5 CPU-only, 6 model-loader, 17 frame-host). You are a different model family from the builder.

## Questions, in order of value
1. **Closure of the second review**: N1 to N6, the mix point and the grammar point: closed, partly, or open, each with file:line and a probe you ran yourself on REAL row manifests (\`$R/rs_rows/out/rows_r2\`, the sealed routing, pose and pointing receipts the tree binds). The materializer must reach its "needs the frame host" marker for every family with no fixture standing in.
2. **Component policy.** Try to break it: an init record with overlap inside the claim scope must refuse; the real init (overlap outside the scope) must be admitted with the scope and the open question's date in the run identity; an evaluation or export on a benchmark outside the scope must refuse; a native evaluation with the deployed selector or a benchmark-chosen rule must refuse until the dated freeze file exists, camera routing on VSTI excepted; training with ground-truth responses must not be gated by evaluation-time choices. Are the records read by hash?
3. **Withheld rooms and room as direct.** Recompute that no admitted row of any family or receipt touches the 80 withheld rooms; check the seeded selection rule and corpus balance; confirm room size has no program row in the bound mix and the allowlist is absolute distance plus three camera types.
4. **The mix actually bound**: the per-step table by type and trace form, expected repeats after all filtering, against the card.
5. **Coverage**: for the 5 CPU-only unexecuted statements, say why a CPU test cannot reach each (or write the three-line test that would); for the model-loader and frame-host statements, check each statically (names, arguments, keys, shapes). Is the single frame-host CPU job complete, bounded and safe?
6. **New faults on the launch path**, and anything else likely to waste an allocation.

## Rules
- Read-only everywhere except your lane folder. No GPU, no launch, no ssh, no agents, no Git commands. Python: \`/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B\`, at most 8 threads; scripts under \`work/\`; lane under 500 MB; this node's disk is low: check \`df\` before any write over 50 MB.
- Never list or search \`/home\` or \`/data*\`. No recursive search outside \`$R/rs_tree\`, \`$R/leg_s1_tree/work/tree_s1\`, \`$R/rs_rows\`, \`$R/rs_cover\`, \`$R/tree_review2\`, \`$R/scene_evidence\`, \`$R/trace_ruling\`, \`$R/b6_build\`.
- No deletion commands, and no names of deletion operations in shell command text. Never read a file over 20 MB whole. Time box: about 60 minutes.

## Deliver
\`out/REVIEW_VERDICT_TREE_R5.md\`: verdict on the first line (\`CODE READY FOR THE FRAME-HOST CPU JOB\`, \`READY AFTER FIXES\` or \`NOT READY\`), the closure table, findings ranked by how likely each is to waste an allocation with file:line, evidence and the smallest fix, the mix table, and what you did not check. One event \`events/<stamp>_RESULT_review.md\` (stamp from \`date -u +%Y%m%dT%H%MZ\` in the writing command), at most 35 lines. Then stay alive 15 minutes checking \`inbox/\` once a minute, and end.
EOF
bash $R/orch_tools/devin_bg_acp.sh /home/jjyeung/agent_project_distill $R/tree_review3/BRIEF.md claude-opus-5-5-high 6000 $R/tree_review3/out/devin_stdout_01.log
grep -v '^rs_tree|' "$S/LANES" > "$S/LANES.new"; printf '%s\n' 'rs_rows|cx:rs_rows||' 'tree_review3|tree_review3/BRIEF.md||' >> "$S/LANES.new"; cp "$S/LANES.new" "$S/LANES"
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import re
p='$S/lanewatch.sh'; s=open(p).read(); s=re.sub(r'\n  \[rs_tree\]=\"[^\"]*\"','',s)
old='  [k1_ops]='; i=s.index(old); s=s[:i]+'  [rs_rows]=\"codex_dispatch.sh implement /scratch/jjyeung/orch_cd/rs_rows \"\n  [tree_review3]=\"tree_review3/BRIEF.md\"\n'+s[i:]; open(p,'w').write(s)"; cp "$S/LANES" "$S/lanewatch.sh" $R/orch_tools/session_scripts_20261115/
echo "- $(date -u +%Y-%m-%dT%H:%MZ) rs_tree fifth pass RESULT 0855Z: component records bound by hash with claim scope and separate training/evaluation gates; room size direct; 80 rooms withheld with no retained overlap; 37 focused tests; coverage 2057/2085 (28 gaps: 5 CPU-only, 6 model-loader, 17 frame-host); strict gate not met; frame-host CPU job written, not run. LAUNCHED rs_rows third pass (Codex Astra high, label rs_rows3: room-size direct rows, superset validator and re-validation, withheld rooms removed) and tree_review3 (Devin claude-opus-5-5-high, 6000 s: closure of the second review on real manifests, component policy, withheld rooms, mix, coverage)." >> $R/ORCH_HANDOFF.md; sleep 3; pgrep -u jjyeung -af '[c]odex_dispatch.sh implement /scratch/jjyeung/orch_cd/rs_rows |[t]ree_review3/BRIEF.md' | cut -c1-70