# so_launch fix round: apply the independent review's findings

Workspace `L=/scratch/jjyeung/orch_n30/so_launch` (yours to write). `$L/PROMPT.md` binds you (read it in full). Review verdict (Cursor Opus, GO AFTER FIXES): `/scratch/jjyeung/orch_n30/so_cr_launch/REVIEW_VERDICT.md` — read it in full first.

Do, each with a regression test that fails before and passes after:
1. Finding 1: withdraw the 120-minute claim everywhere; state plainly that patch 01 cannot hit in the production topology and must stay OFF. Write `$L/out/CROSS_RUN_STORE_DESIGN.md` (one to two pages): the safe cross-run design the review lists (content-addressed preparation store readable by every Orchard node, key computed by the native preparation over exactly the inputs it reads with a field recorder that refuses unkeyed fields, receipts without run paths, an adopt step that regenerates request/config/source seal/data_receipt for the new run, cross-node checkpoint bindings, two-node cold-build determinism check, the independent admission review), with an estimate of minutes saved per launch (labelled estimate; mode p measured 140.57 and 145.27 min) and what each piece costs to build.
2. Finding 2: a MISS never touches the destination; quarantine only on the HIT path right before the verified rename; invert the test so a partial native journal and a foreign-config journal survive a miss.
3. Finding 3: correct the report; patch 03 (checkpoint verification memo) ranks first, with the 4-10 min per resume launch estimate and the four `complete()` calls it explains (the 11-minute gap).
4. Finding 4: lock marker instead of readlink comparison; `flock -w 600 7 || exit 75`; tests for a symlinked parent and a duplicate job.
5. Finding 5 and 7: one wrapper test that sources the real `c.sh` `tk_stage` with stubbed helpers; add the omitted native test modules to the gate.
6. Finding 6: guard `o/` and add timing around the `r.sh` `g.py` calls.
7. Finding 8: drop the R2-only environment names from the key tuple; assert no model/method word in any written JSON name or field name.
8. Regenerate patches and manifest; rerun every test with exact outputs; rewrite `$L/out/REPORT.md` (first line `VERDICT: ...`) and `$L/out/NOTE_FOR_TREE_REBUILD.md` (order: 03, 04, 02; 01 stays OFF) with a section "Review round 1: finding -> fix -> test".
Due 09:30Z 2026-11-19; `date -u` at each step. Local sockets are not available in your sandbox.
