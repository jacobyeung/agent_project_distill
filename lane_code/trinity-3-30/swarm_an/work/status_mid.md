## Verified and in the record (none failed)
- First wave, 18 of 18. Deep Codex, 18 of 18: disthead, countform, dirform, frames, vsti, size, reldist, room, deep2_apporder, deep2_route, deep2_vstivis, deep2_gapbands, deep2_camhead, deep3_countsingle, deep3_reldist_join, deep3_size_decomp, deep3_dirtw_bits, deep3_xroom. Devin Opus, 7 of 7: san_dd_dist, san_dd_count, san_dd_dir, san_dd_app, san_dd_reldist, san_dd_size, san_dd_dirtw. Refuter (Codex): 32 of 34 numbers matched; its corrections are in the text.
- Session 3 (third deep wave, 05:48Z to 06:20Z) is record sections 10.16 to 10.24, Answer item 9, section 5 changes 9 to 12 and five "not row changes" lines, section 6 (new label defects), section 8. Two analyst numbers corrected in the text: deep3_xroom priced appearance order as a ReVSI category (worst 20 rooms hold 6.50 ReVSI points, not 8.36) and its "no room effect on dev-S1" holds only with rooms weighted equally (p = 0.008 weighted by items).
- My session-3 recounts: work/verify/deep3_recount.py [count reldist size dir xroom stable] (outputs DEEP3_RECOUNT_m200.txt, STABLE_m200.txt), xroom_recount.py. Generator of the wave's prompts and briefs: kit/make_deep3_prompts.py (head and tail cut from m200_deep_room.md and briefs/san_dd_app.md; a PRICE block states the benchmark mapping, to which "ReVSI has no appearance-order category" must be added when reused).

## Sent
- events/swarm_an RESULTs: 0512Z, 0537Z (session 2), 0620Z (third deep wave verified).
- events/swarm_build NOTEs: 0457Z, 0503Z, 0506Z, 0507Z, 0524Z, 0537Z (sessions 1 and 2); 0609Z (third wave: bars for a count head and a size head, counting row mix, relative distance, frames) and 0620Z (Devin reads; withdraws the 0609Z estimate of 80% for routed relative distance; size rows are ScanNet++ only; small-object rows; hard-pair rows; no rewording of the toward line; the toward-only skeleton reached away items between steps 100 and 200).
- Orchestrator rulings received: ORDER 0457Z, ORDER 0515Z (see the record's sections 5 and 12). No ruling has arrived since; the inboxes are empty.

## Running
Nothing. tmux san_q6 has drained; the three Devin lanes have written DONE.

## Next steps, in order
1. Step-400 reads. Lane cont_ops18 posts fetched paths in B/events/cont_ops (its STATUS.md: export about 08:30Z; direct read h1read7 token a59a7bff4c4 first, then facing h1face7 afdfd5caac6 and VSTI h1vsti7 a4525db2f6a, then the routed read). When a return is fetched: write kit/roots.json ({"direct": {"R1,400": ".../fetched/x"}, "facing": {...}, "vsti": {...}}), check `K.direct('R1', 400, 'dev-S1')` loads and `K.summary` agrees with the return's SUMMARY.json, run `category_points.py 400` and `change_points.py 400`, then queue the analysts whose set has arrived: `bash kit/run_queue.sh work/queue_m400.txt` in tmux (16 prompts written by make_prompts_next.py; split the queue file by set if returns arrive apart; the three routed analysts and cot_cost need the routed return wired into san_kit.routed(), which reads through score_r5 with step-specific paths). Verify each, append a dated section "Step 400" to the record (per type: modes at 544, 200, 400 in type and benchmark points; the gates below), RESULT. To add step 400 to my recounts, add ('R1', 400) to the `D` dict of work/verify/deep3_recount.py.
2. Gates to read first at step 400 (step-200 values):
   - force-closed counting items 28 of 150 dev-S1, 83 of 385 R0-dev, 65 of 139 relative count (the test of procedure-only counting that the 0515Z ruling waits for);
   - counting form and mix: non-looping traces in the procedure-only form 6 of 347; single-category non-looping score against a constant 2 (R0-dev 72.0 against 73.5, dev-S1 68.3 against 71.3); truth-2 items right 126 of 145 and 61 of 76; truth-3 undercounts 33 of 47 and 16 of 25;
   - away traces with the "Step 1: find" opening 43 of 202 (0 at step 100) and omitting the turn 42; hard away right 36 of 71;
   - metre distance calls 36 of 43 and all units 88 of 150;
   - traces citing a frame above 32: 100 of 246 appearance order, 373 of 900 VSTI;
   - overcounts at truth 2 on R0-dev multiple 24 of 44; appearance-order answers equal to the frames decoder 230 of 246;
   - size: dev-S1 by dataset (ScanNet 56.6 on 32, ScanNet++ 65.0 on 42, ARKitScenes 77.2 on 76; the size rows are ScanNet++ only); R0-dev answer over truth under 30 cm 1.19 and at 250 cm or more 0.70;
   - relative distance where step 544's margin is under 1.25: 48 of 101 right;
   - R0-dev toward: 115 wrong of 376; the 69 always-wrong items (how many keep their option).
3. While the export is awaited (optional, at most 5 Codex and 3 Devin at a time, each verified before it is passed on): a Devin read of the VSTI camera-object types (11.0 VSTI points; two Codex passes exist, record 10.5 and 10.13); a paired look at R0-dev label geometry if the orchestrator names the R0-dev build record (object centres), which would settle whether the toward errors lie inside the training rows' 5- and 10-degree margins (record 10.24, section 8).
4. Rotate 5.5 hours after start or at 60% of context (brief, last paragraph).

## Spend
37 Codex Astra-high dispatches finished (17,055 wall seconds; no dollar figure in the log); 7 Devin Opus sessions finished; Fable sessions 1, 2 and 3.
