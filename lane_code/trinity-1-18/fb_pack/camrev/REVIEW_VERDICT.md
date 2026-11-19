**Verdict: GO.** No MUST items. I found no defect in the 5,979 rows, and four SHOULD items follow.

# fbp_camrev review of fb_pack/cam

I checked every row with my own code on trinity-1-18 (CPU, nice 10): `/tmp/camrev_work/diffcheck.py`, `heldout.py` with a full-DP C Levenshtein (`lev.c`), and `run_intake.py`. None of them imports packet helpers.

## Verified
1. **Only the two line forms changed.** A recursive JSON diff of each output row against its input row (same order, same qid) finds changes only in `target`, plan/canonical_text `text`, `tool_output_spans[].start/end`, and the added `provenance.camera_trace_edit`. Every changed text and every target equals my own rewrite of the input. That rewrite swaps the rotation sentence and drops ` = v m` only after `-d[xyz]` on the Scoring line. No other target line differs, and calls, tool-response bytes and values, question, options, answer, GT and poses are identical.
   - Edits: 1,993 rotation + 1,988 direction = 3,981 rows. All 1,994 displacement rows are untouched, as are 4 two-option direction rows with no negated option (e.g. `cbc70c796bedadc95762ce5cc-sbca-t13`, rows line 4081).
   - Four edited direction rows already passed the grammar before the edit: `c62d9047f4fde9b79fc189236-sbca-t18`, `cac6c402eb7dd1b1d27e34c69-sbca-t15`, `ce38cd2c632a32bd4cfae8625-sbca-t34`, `scale-native-0c8691a956bcc982ee80fe7c764fe4fc-sbca-t33`. Editing them too is correct for a uniform rule.
   - The input (`31914ba5…`) and output (`e8cbda99…`) hashes match BUILD.json.
2. **Grammar and intake.** The SHA256 of `trace_grammar.py` matches the pinned `a41ba191…`. I ran the unmodified `r2_intake.intake(limit=2000)` on all three shards, whose bytes concatenate to the delivered rows file.
   - Result: 1,723 / 1,725 / 1,695 admitted and 277 / 275 / 284 refused. Every refusal is `excluded:eval_rooms`, and the refused qids equal those in INTAKE.json.
   - `r2_intake.py:102` runs the shared grammar before the exclusion check at `:104`, so all 5,979 rows pass the grammar.
   - The exclusion, withheld-room, dev-scene and extent pins equal the route envelope's. The tree wrote no file during the run.
3. **Answers recomputed from printed responses.** There are 0 mismatches between answer, gt_answer and the final answer.
   - Displacement (1,994 rows): the answer equals the printed distance, which matches sqrt(dx²+dy²+dz²) within rounding.
   - Rotation (1,993 rows): the answer equals the printed turn, and every turn lies in (-180, 180].
   - Direction (1,992 rows): the option with the largest signed score is the answer, and "The largest is X. That matches option Y." agrees.
4. **The edited lines still lead to the answer.**
   - Ties: no direction row has a printed tie, and the winner beats the next option by at least 0.10 m on every row.
   - Values: the remaining direct values equal the response components. Every removed negated value equaled minus its component, so the edit removed nothing wrong.
   - Near-equal magnitudes: in 24 rows a second axis comes within 0.10 m of the dominant axis, but that axis is never offered, so no decision depends on a sign the line hides. The signed-score rule and the largest-magnitude rule pick the same option on every row.
   - Readability cost: in 792 rows the winner is a negated option, so its value is no longer printed anywhere in the trace. For 54 negated items the reader must take the component from the tool response, because the line has no positive twin.
   - Rotation: "shortest signed turn, positive meaning left, half turn reported as positive" states the same convention as (-180, 180] with left positive. No row has |turn| = 180, so the tie clause is never exercised. No row's text contradicts its values.
5. **Held-out guarantee.** The gate pins match HELDOUT_CAMERA_ITEMS, HELDOUT_CAMERA_TWINS, HELDOUT_NATIVE_TASKS and WORDINGS (gate text hash below).
   - Each of the 450 reworded items equals its h-template instantiated exactly, giving 24 distinct normalized wordings.
   - I recomputed the filter with sb_rowA's normalization and Levenshtein distance divided by the longer length. No pair falls below 0.20, either against the actual items or against all 24 templates instantiated with each row's frames and options. The closest pair is 0.449 (direction), and the same-type minima are 0.504 (displacement), 0.455 (rotation) and 0.449 (direction).
   - Every training question matches exactly one t-template (agreeing with its qid suffix) and no h-template, giving 40 wordings per type.
   - After eval-room refusals, the cells hold 38–49 rows each (displacement 1,717, rotation 1,722, direction 1,704), identical to CELLS.md. No row shares a room with the 37 held-out rooms.

## SHOULD
**S1. Two prose forms reach N. This is a moderate training hazard.**
- Evidence: `compose()` keeps base routing rows (`r1_routing.py:110-115`) and drops only the slice cells recovery, absolute_distance and units (`r1_population.py:29`). Base rows skip r2 intake, and `carrier_c1_run.py` never imports the shared grammar.
- The P extract carries the old forms in 2,000 of 2,000 rotation rows and 1,996 of 2,000 direction rows (SOURCE_FORMS.json). Per sb_rowA's REPORT.md, each row here is one of those sources with only the question reworded.
- So unless N's exclusions drop those sources, N trains on paired rows whose line form follows the wording family: native wordings get the numeric form and sbca wordings get the symbolic form.
- Rotation: the convention sentence sits in the plan before `<turn>`, so the form choice comes before the call the gate measures.
- Direction: the symbolic form trains the model to negate components without writing the result. All 300 gate direction items use the options backward/right/left/forward, so every item has two negated options.
- Gate risk: arms (a) and (b) may then differ in prose form as well as wording, which would confound a transfer verdict.
- How a read shows it: tag each routed camera trace's convention sentence and scoring line as numeric, symbolic or hybrid (e.g. `-dz = -0.68 m`). Cross-tabulate form × arm × type with call rate and score. For direction, split accuracy by the sign of the gold option and count opposite-sign picks on the gold axis.
- The hazard shows up as different form shares in (a) and (b), opposite-sign errors concentrated in symbolic traces, or missing calls after hybrid plan sentences.
- Fix: the tree owner applies both rules to the base camera rows at composition (the rules preserve values, as verified above), or the gate read carries this split before N's decision.

**S2.** The delivered rows file still holds the 836 eval-room rows (REBIND.json `excluded`). They stay out of training only while every consumer goes through r2 intake, which `compose_native` does (`r1_routing.py:191`). Ship the admitted-qid list beside the rows, or flag it in PACKAGE.json.

**S3.** `REPORT.md:76` lists the gate text's hash as MISSING. The file I read once hashes to `6f0da4881dc640c0d80967d1a44f26a85da437149a58de2e32066affaffa84ba`; record it.

**S4.** All 120 cells are below the target of 50 (38–49 rows), a total deficit of 857 rows: 21 inherited from the input and 836 eval-room refusals. Per-wording training exposure is therefore about 14% below what the gate text's "6,000 rows" implies. The held-out cells are unaffected.
