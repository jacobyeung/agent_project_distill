# evalx27 STATUS (trinity-1-3; operator evalx28 since 20:38Z) - for a successor
Updated: 2026-11-15T20:33Z (evalx27 stopped on ORCH 2027Z; successor evalx28)

## VSI-Bench official direct read (job 1) - DONE (evalx28)
- 170008 COMPLETED 20:31:01Z; fetched to work/kit/build/a8acc277397 (packet/ extracted; ANALYSIS.txt). result.tar.gz sha256 4609adde0bb8a9ee734abacd29ac4df03766d4c48bf0bf0fa90552627500065f. Mirror trinity-1-13:/scratch/jjyeung/n30_mirror/evalx27/a8acc277397 (sha equal). Copy events/evalx27/prod_a8acc277397/.
- B2048 six-task mean 68.77 [66.5,71.0]. Record distill_design/OFFICIAL_VSI_DIRECT_STEP544_20261115.md + INDEX line; RESULT event 20261115T2050Z. Orchard return pool okh7/x27ret/a8acc277397 left in place.

## ReVSI direct read (job 2) - DONE (evalx28)
- Production 170037 COMPLETED 21:36:39Z; five-category mean B2048 64.94 [61.3,68.4]. Packet work/kit_revsi/build/a348bc58686 (ANALYSIS.txt); return sha 785a097ff750fc3d82a5ffd18cb299527fbe1e207d5166c86326edddd21c2036; mirror trinity-1-13:/scratch/jjyeung/n30_mirror/evalx27/revsi/ (sha equal); copy events/evalx27/prod_a348bc58686/. Record distill_design/REVSI_DIRECT_STEP544_20261115.md + INDEX; RESULT 20261115T2141Z.
- History of this job below.
- F1 DONE: kit ea1a1b2d5b965017f7cacce9c02c13cbbe5522d87be8cc55ab755176ecd55d3b (work/kit_revsi/package.tar; copy events/evalx27/kit_revsi_ea1a1b2d/). Evidence RESULT 20261115T2102Z. review_rv verdict sha 256ec41b35056f3a12e847273739f298d68f51aaec2de2f6b30789fbc4bdce17.
- Governor: helpers in /scratch/jjyeung/io_governor; node agent tmux iogov_agent (/scratch/jjyeung/io_governor_serial) started 20:52Z on trinity-1-3.
- JOBS SUBMITTED 21:11-21:13Z: proof 170035 (a15_cot_appb906babb42, 2 h, dest work/kit_revsi/build/pb906babb42) and production 170037 (a15_cot_apa348bc58686, 6 h, afterok:170035, dest work/kit_revsi/build/a348bc58686). RESULT 2115Z. Notice to main written. Poll every 10 min; on proof return fetch + read COMPLETE/PARITY; scancel 170037 if Phase A fails. On production return: fetch (>=20 MB needs registered stream), extract packet/, `python3 work/analyze_revsi.py <packet>`, record + INDEX + RESULT, mirror to trinity-1-13.
- Proof 170035 COMPLETED 21:23:40Z (9 min): EXIT COMPLETE; videos verified 261; frame plan 261; PARITY prompt bytes 20/20 equal, processor checked; CHECKS passed. Packet work/kit_revsi/build/pb906babb42/packet; copy events/evalx27/proof_pb906babb42/ (sha fd037e9e...). Production 170037 RUNNING since 21:23:55Z on orchard-community-0.
- Media DONE: Orchard /project/community/jjyeung/okh7/313db5a47f11ff0c/ verified 261 files (tar sha ad3635ff...; both governor records .done).
- (done) Media READ stream: tmux x27_media_read, work/media_stream/launch_read.py (gated_tar.py, deterministic USTAR byte-equal to make_archive.py, pin-checked | ratelimit.py > <HEX>.tar.part), record streams/evalx27_rv_media_read.json, priority 25, registered 20:58:16Z, expected 318,453,760 B. HEX=313db5a47f11ff0c (work/media_stream/HEX). On success: <HEX>.tar + TAR.json (sha). Then rename record to .done.<epoch>.
- Media UPLOAD stream (to register once tar exists): gated_reader.py <HEX>.tar | ratelimit.py | ossh.sh "set -e; test ! -e /project/community/jjyeung/okh7/<HEX>.tar; umask 077; set -C; cat > .../<HEX>.tar", --kind push --io-weight 1 --priority 25. Then one Orchard call: sha256 check, mkdir okh7/<HEX>, tar xf, check_on_orchard via stdin (kit_revsi/PROOF_JOB.md).
- Proof prepared: token pb906babb42, dest work/kit_revsi/build/pb906babb42 (plan 2c946cb4..., media root /project/community/jjyeung/okh7/313db5a47f11ff0c, --skip-phase-b, 2 h). Submit per PROOF_JOB.md; then production (fresh token, --mode production, afterok) on general. Write tests, ledger, notice to main, verdict + kit sha in submit event.
- Reporting R1-R5 (review_rv): report/*.json only; five-category mean never against 58.63 or 57.5; per category unpaired beside parent recovered B2048 (route 42.86, size 63.41, direction 48.43; counting and rel. distance not recovered); state checkpoint, batching (32/16 vs 128/64) and cohort-size (679 vs 999) differences; check processed-size/visual-token distributions; toward/away split diagnostic. Record distill_design/REVSI_DIRECT_STEP544_20261115.md + INDEX.

## Other
- Orchard ledger: work/ORCHARD_LEDGER.jsonl. Orchard temp to clear by user: okit/tmp/x27*, okh7/x27tmp. REMOVAL_CANDIDATES.md lists them.
- Notes written: events/k1_ops3/STEP544_EXPORT_ON_ORCHARD.md; events/evalx27/GCS_TRANSPORT_NOTE.md (for cont_ops2); ORCHARD_INVENTORY.md.
- At hand-over the ReVSI F1 Codex pass was still running (pgrep -f evalx27_revsi_f1); let it finish, then read kit_revsi/F1_EVIDENCE.md.

## Lane state 21:41Z
- Both jobs of the lane are done and reported. No job of ours is on Orchard. Node agent iogov_agent remains on trinity-1-3 (leave it; other lanes on this node may register). Waiting for orchestrator orders.
