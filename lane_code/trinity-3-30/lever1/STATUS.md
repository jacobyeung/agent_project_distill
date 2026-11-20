# lever1 STATUS (trinity-3-30; started 16:50Z 11-20; 6 h timeout -> write B/briefs/lever2.md and start lever2 by ~22:20Z)
Lane dir /scratch/jjyeung/orch_n30/lever1 (work/, out/); 2-28 work dir /scratch/jjyeung/orch_n30/lever1_c; 1-18 helper dir /scratch/jjyeung/orch_n30/lever1_m.
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
