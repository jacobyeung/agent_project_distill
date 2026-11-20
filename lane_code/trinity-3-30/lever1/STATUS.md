# lever1 STATUS (trinity-3-30; started 16:50Z 11-20; 6 h timeout -> write B/briefs/lever2.md and start lever2 by ~22:20Z)
Lane dir /scratch/jjyeung/orch_n30/lever1 (work/, out/); 2-28 work dir /scratch/jjyeung/orch_n30/lever1_c; 1-18 helper dir /scratch/jjyeung/orch_n30/lever1_m.
## Done
- Rank 2 round 4 + BOX RESULT (C1 waits both ways; vote box +5.65 clears held-out bar, dev check pending); record updated.
- Rank 6 RESULT (route table stays; constant 31.5); rank 3 STOP RESULT (i ok, ii 2.59 fails); rank 2 review DEFECT RESULT; record updated for all.
- Rank 2 RESULT 1824Z (parity PASS; geometry waits for masks; arm B/C closed; G3T stays); record updated. Rank 3 parity STOP QUESTION; record updated.
- Item 0 selector provenance: RESULT 1654Z (out/SELECTOR_PROVENANCE.md; events/lever/files/). run_iso 6d97c524, K1 train only; 0 benchmark/dev rooms; 4 withheld-80 rooms.
- Item 1 inventory: out/ARCHIVE_INVENTORY.md; QUESTION 1659Z; ORCH ANSWER 1700Z: (a) IB mirror now, (b) one compressed archive via governor later (to /data2 or /data3, whichever has more free), add path to D/INDEX.md under the plan line.
- trinity-1-3 /scratch/jjyeung is gone. 3-30 /scratch 83 GB free: no mirrors here.
## Running (2-28 tmux; poll work/poll228.sh via tssh every 5-10 min)
- Rank 1 fix round 3: tmux l1_r1fix2 (BRIEF_R1FIX2.md). Then 3rd review (BRIEF_R1REV2-style), place via ossh, CPU check, ONE general job (<= 40 min alloc), pull_depth.sh, relift.py (56 items/28 captures), BOX dev check (vote_10_3_best).
- Rank 4 probe kit build: tmux l1_r4kit (BRIEF_R4KIT.md; in/ = D400 package + dk + WORD_TEMPLATES.json). Runs on general after rank 1's job (ORCH 1709Z, <= 30 min).
- Rank 5: blocked at reproduction (no raw for reference captures); QUESTION 19:3xZ for a 1.24 GB stream (scene0166_00 .sens etc, 17c5e6a336, 41069053); default stage at 20:00Z, then rerun BRIEF_R5.md.
## Done
- Rank 6 RESULT (route table stays; constant 31.5); rank 3 STOP RESULT (i ok, ii 2.59 fails); rank 2 review DEFECT RESULT; record updated for all.
- Rank 2 RESULT 1824Z (parity PASS; geometry waits for masks; arm B/C closed; G3T stays); record updated. Rank 3 parity STOP QUESTION; record updated.
- Item 0 selector provenance: RESULT 1654Z (out/SELECTOR_PROVENANCE.md; events/lever/files/). run_iso 6d97c524, K1 train only; 0 benchmark/dev rooms; 4 withheld-80 rooms.
- Item 1 inventory: out/ARCHIVE_INVENTORY.md; QUESTION 1659Z; ORCH ANSWER 1700Z: (a) IB mirror now, (b) one compressed archive via governor later (to /data2 or /data3, whichever has more free), add path to D/INDEX.md under the plan line.
- trinity-1-3 /scratch/jjyeung is gone. 3-30 /scratch 83 GB free: no mirrors here.
## Running (2-28 tmux; poll work/poll228.sh via tssh every 5-10 min)
- Rank 1 fix round: tmux l1_r1fix (BRIEF_R1FIX.md; 4 review findings). Then re-review (work/briefs/BRIEF_R1REV.md again), place via ossh (/dev/shm staging on 3-30; o_place.sh 8.5 MB), CPU check, ONE general job, pull_depth.sh (governed, io-weight 1) to 2-28, relift.py.
- Rank 2 round 4 (GT-depth fix, C1 two ways) + BOX follow-up: tmux l1_r2e (BRIEF_R2E.md, BRIEF_R2D.md).
## Queued
- Rank 5 build: work/briefs/BRIEF_R5.md when a build slot frees.
- Rank 4 read: after rank 1's job; templates out/WORD_TEMPLATES.json; build a 64-token probe kit at step-400 init 5083243c.
## Done
- Rank 2 RESULT 1824Z (parity PASS; geometry waits for masks; arm B/C closed; G3T stays); record updated. Rank 3 parity STOP QUESTION; record updated.
- Item 0 selector provenance: RESULT 1654Z (out/SELECTOR_PROVENANCE.md; events/lever/files/). run_iso 6d97c524, K1 train only; 0 benchmark/dev rooms; 4 withheld-80 rooms.
- Item 1 inventory: out/ARCHIVE_INVENTORY.md; QUESTION 1659Z; ORCH ANSWER 1700Z: (a) IB mirror now, (b) one compressed archive via governor later (to /data2 or /data3, whichever has more free), add path to D/INDEX.md under the plan line.
- trinity-1-3 /scratch/jjyeung is gone. 3-30 /scratch 83 GB free: no mirrors here.
## Running (2-28 tmux; poll work/poll228.sh via tssh every 5-10 min)
- Rank 1 build: tmux l1_r1 (brief lever1_c/BRIEF_R1.md); next: Astra review, place/CPU check/submit ONE general job, fetch, relifts (72 items first).
- Rank 3 round 2 diagnostics: tmux l1_r3b (BRIEF_R3B.md; ORCH 1827Z): (i) rigid no-refit ~0, (ii) GT-gravity L1; amendment file out2/AMENDMENT.md before the single read; else stop.
- Rank 2 review (read-only): tmux l1_r2rev (BRIEF_R2REV.md; ORCH 1826Z item 2): ARKit GT-depth mechanism; C1 enters no decision until it reports.
## Queued (start as build slots free; max 2 builds on 2-28)
- Rank 2 BOX follow-up: work/briefs/BRIEF_R2D.md (registered in the plan record 18:40Z).
- Rank 5 build: work/briefs/BRIEF_R5.md (raw staged: lever1_c/nogt/raw, 545 files, stream sha c1d7e30e; record renamed .done).
- Rank 6: work/briefs/BRIEF_R6.md (inputs lever1_c/r6/in).
- Rank 4 read: templates frozen in out/WORD_TEMPLATES.json (one template, sha 71e4834d; ReVSI = VSI-Bench wording per Table 9); still to freeze: call detector, 64-token budget, 95% gate; needs a probe kit at step-400 init (5083243c) after rank 1's job.
## Done
- Item 0 selector provenance: RESULT 1654Z (out/SELECTOR_PROVENANCE.md; events/lever/files/). run_iso 6d97c524, K1 train only; 0 benchmark/dev rooms; 4 withheld-80 rooms.
- Item 1 inventory: out/ARCHIVE_INVENTORY.md; QUESTION 1659Z; ORCH ANSWER 1700Z: (a) IB mirror now, (b) one compressed archive via governor later (to /data2 or /data3, whichever has more free), add path to D/INDEX.md under the plan line.
- trinity-1-3 /scratch/jjyeung is gone. 3-30 /scratch 83 GB free: no mirrors here.
## Running (2-28 tmux sessions; poll with one batched tssh every 5-10 min: work/poll228.sh)
- Rank 3 DEV-POSE: tmux l1_r3 (Codex receipt codex_local/.../20261120T170111Z_lever1_r3), out lever1_c/r3/out/REPORT_R3.md.
- Rank 2 K1-X round 3: tmux l1_r2c (briefs lever1_c/BRIEF_R2{,B,C}.md); amendment registered in the plan record 17:42Z (served program, parity 56.77/73.97; ORCH ANSWER 1719Z).
- Rank 5 raw stream: governed lever1_nogt_raw (2-28, list lever1_c/nogt/list.txt, 545 files 8.28 GB) into lever1_c/nogt/raw; stage.log gets PIPE_RC when done; then rename streams/lever1_nogt_raw.json -> .done.<epoch>. Build brief work/briefs/BRIEF_R5.md (inputs DEVS1_MANIFEST.json, GT_RASTER_BUILDER_CR.tar.gz already in lever1_c/nogt/).
## Done
- Item 0 selector provenance RESULT 1654Z. Item 1 archive: (a) mirror 2-28 n30_mirror/lever1 (RESULT 1709Z); (b) /data3/jjyeung/distill_archives/lever1/k1x_inputs_20261120.tar.zst done 17:47Z, verified d2dd7a40, .sha256 + MANIFEST beside, INDEX line added.
- Rank 4 review LEGAL WITH CONDITIONS (ORCH 1709Z: read after rank 1's job, step-400 init 5083243c, <= 30 min general; freeze+hash templates first; arm D closed). Rank 5 bytes RESULT; build approved (ORCH 1715Z: one governed read, 150 GB free on 2-28, half-extent per capture, second small archive after, rank 1 reads 72 first).
- Plan record: Results section (selector, archive, rank 2 amendment, rank 4, rank 5 bytes).
- Rank 6 inputs staged: 2-28 lever1_c/r6/in (corpus reads, INDEX, meta, tool; stream sha c257a1c3 both ends); brief work/briefs/BRIEF_R6.md (also in r6/in/briefs/).
- Accident: work/r6in.tar (8 GB) on 3-30; deletion queued by rm_guard; REMOVAL_CANDIDATES.md.
## Next
- Rank 1 build (brief work/briefs/BRIEF_R1.md) when a Codex slot frees (max 2 on 2-28); then Astra review, CPU check, ONE general job, CPU relifts.
- Rank 6 ledger (Codex) after; rank 4 read after rank 1's job (templates need ReVSI public text source).
- Record: results sections in D/ROUTED_READER_LEVER_PLAN_20261120.md per rank (+ R0 exclusion open item).

## 20:12Z ROTATION (exact)
- lever1 hands off to lever2 (brief B/briefs/lever2.md; started on trinity-3-30). Rank 5 RESULT posted (15/22 pass). In flight on 2-28: tmux l1_r1fix3 (rank 1 fix round 4). Nothing of lever1's runs on Orchard or GPUs; no governed stream open (lever1_nogt_raw, lever1_nogt_ref, lever1_k1x_archive all .done).
- Next steps for lever2 are listed in B/briefs/lever2.md (rank 1 review/job/relift + BOX dev check; rank 4 kit fix/review/job; rank 5 mirror/archive/ARKit restage).
