# Build 8 status

Items 1–8 are implemented or retain their named blockers below. The final packet suite passed all 202 tests (`proofs/packet/results.json`). The final frozen package suite is active, using the archive pinned in `DELIVERY.json`. All 30 focused repair checks passed and current-source CPU gaps are zero (`proofs/final_repairs/results.json`, `CHANGED_COVERAGE.json`). Both kits were rebuilt from empty, A2 first, with GO=false (`kits/RESULTS.json`). No remote action or GPU use.

Step 1: fixture regressions pass; BF16_CACHE_GRADIENT_PARITY remains blocked at its original tolerance. Evidence: `work/build8/proofs/regressions/DISPOSITION.json` and `BF16_PARITY.json`.

Step 2: both inherited R2 failures pass. The diagnostic frozen comparison records zero R2 failures (`DIAGNOSTIC_SUITE_COMPARISON.json`). The final frozen R2 group is active after the completed legacy group (`final_package.log`, `proofs/suite_tree/r2/progress.json`).

Step 3: Native producer/reader proofs close every CPU gap, including cache writing/reading/row encoding, pose validation, direct-source CLI and both own-value routes (`proofs/final_repairs/results.json`, `GAPS.json`). External classifications retain file:line reasons. Final coverage aggregation follows the frozen suite.

Step 4: The local attempt failed because the sandbox refused sockets (`proofs/stop_multirank/RESULT.codex_sandbox.json`). A separate lane receipt reached the first step, then failed at the signal helper path (`RESULT.json`). The prepared driver repairs that path; it has not been rerun. Lane runs `proofs/stop_multirank/RUN.sh` after build 8. Stop/export/reload remain unproved.

Step 5: Local frame-dimension fixes pass native tiny-model proofs at 32 and 64 in proofs/frames and proofs/frame_stream. Full camera selection still needs the sealed goal-scene exclusions; canonical GTScene admission and full model/processor inputs remain external qualification blockers.

Step 6: Every inherited transform-review entry now has a classification and file:line reasoning in proofs/audit/RESIZE_AUDIT.json. Distorting paths remain recorded defects; portrait share unknown: frame dimensions absent from the bound slices. Mask coordinates were unchanged; row-byte parity was not measured.

Step 7: Legacy direct-source and training-suffix paths refuse empty or whitespace think bodies with LEGACY_DIRECT_SOURCE_EMPTY_THINK_REFUSED. Concrete traces preserve their target bytes. Native producer/SQLite reader proofs pass in proofs/direct/results.json. Bound R2 admission code is unchanged.

Step 8: D2 init selection, D3 store bindings, D4 real dense manifest, row text/minority forms, in-forward EAT A2-A4 work, production processor values and BF16 enablement remain named blockers. Faithful bound-row identity also remains blocked; the native preparation proof records gt_decision_mismatch.

staging: running (`work/build8/FINAL_PASS.json`).

Both kits are staged from empty, A2 first. Hashes and input blockers: `work/build8/kits/RESULTS.json`. No init or dense fixture was substituted.

staging: complete (`work/build8/FINAL_PASS.json`).

review_evidence: running (`work/build8/FINAL_PASS.json`).

review_evidence: complete (`work/build8/FINAL_PASS.json`).

audit_code: running (`work/build8/FINAL_PASS.json`).

audit_code: complete (`work/build8/FINAL_PASS.json`).

resolve_resize: running (`work/build8/FINAL_PASS.json`).

resolve_resize: complete (`work/build8/FINAL_PASS.json`).

legacy_guard_proof: running (`work/build8/FINAL_PASS.json`).

legacy_guard_proof: failed (`work/build8/FINAL_PASS.json`).

Final validation: seal running; evidence `work/build8/FINAL_PASS.json`.

Final validation: seal complete; evidence `work/build8/FINAL_PASS.json`.

Final validation: make_delivery running; evidence `work/build8/FINAL_PASS.json`.

Final validation: make_delivery complete; evidence `work/build8/FINAL_PASS.json`.

Final validation: packet running; evidence `work/build8/FINAL_PASS.json`.

Final validation: packet failed; evidence `work/build8/FINAL_PASS.json`.

Final validation: package running; evidence `work/build8/FINAL_PASS.json`.

Final validation: package failed; evidence `work/build8/FINAL_PASS.json`.

Final validation: supplemental running; evidence `work/build8/FINAL_PASS.json`.

Packet input references and fresh pytest workspace are installed. The packet and frozen package suites completed; receipts are in proofs/packet and proofs/package. The recovery sequence is recorded in PACKET_RECOVERY.json.

Current-source focused verification passed (`work/build8/proofs/final_targeted/results.json`).

Final validation: supplemental complete; evidence `work/build8/FINAL_PASS.json`.

Final validation: guards running; evidence `work/build8/FINAL_PASS.json`.

Final validation: guards complete; evidence `work/build8/FINAL_PASS.json`.

Final validation: compare running; evidence `work/build8/FINAL_PASS.json`.

Final validation: compare complete; evidence `work/build8/FINAL_PASS.json`.

Final validation: coverage running; evidence `work/build8/FINAL_PASS.json`.

Final validation: coverage complete; evidence `work/build8/FINAL_PASS.json`.

Final validation: eat1_scan running; evidence `work/build8/FINAL_PASS.json`.

Final validation: eat1_scan complete; evidence `work/build8/FINAL_PASS.json`.

Final validation: eat1_c8r running; evidence `work/build8/FINAL_PASS.json`.

Final validation: eat1_c8r complete; evidence `work/build8/FINAL_PASS.json`.

Final validation: eat1_gf1 running; evidence `work/build8/FINAL_PASS.json`.

Final validation: eat1_gf1 complete; evidence `work/build8/FINAL_PASS.json`.

The diagnostic frozen R2 group passed all 384 tests (`proofs/suite_tree/r2/results.json`). The comparison records the retained BF16 failure and two assertion events from the repaired single-image error message (`SUITE_COMPARISON.json`). Exact-source coverage requires fresh cache proof receipts after the cache validator edit. Native cache CLI/writer/reader tests now live in `tests/test_r2_build8_cache.py`; the direct-source proof invokes the real CLI. Focused frame, cache, direct and original single-image checks are running before any new staging (`final_repairs.log`).

Both kits are staged from empty, A2 first. Hashes and input blockers: `work/build8/kits/RESULTS.json`. No init or dense fixture was substituted.

The single-image message repair and native malformed-frame/pose/FoV cases passed (`proofs/final_repairs/results.json`). Both kits were rebuilt from empty, A2 first. A fresh frozen pass follows.

Final validation: seal running; evidence `work/build8/FINAL_PASS.json`.

Final validation: seal complete; evidence `work/build8/FINAL_PASS.json`.

Final validation: make_delivery running; evidence `work/build8/FINAL_PASS.json`.

Final validation: make_delivery complete; evidence `work/build8/FINAL_PASS.json`.

Final validation: packet running; evidence `work/build8/FINAL_PASS.json`.

Final validation: packet complete; evidence `work/build8/FINAL_PASS.json`.

Final validation: package running; evidence `work/build8/FINAL_PASS.json`.
