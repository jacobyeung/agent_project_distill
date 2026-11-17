# Build 8 status

Items 1–8 are implemented or retain their named blockers below. The packet suite passed all 202 tests (`proofs/packet/results.json`). The frozen diagnostic package suite is active. It found an error-message regression in the single-image guards; the working tree now preserves the original “32 pinned” assertion while naming both supported frame counts. Native malformed-head and row-shape cases are also added. Their focused check and a new freeze/final pass remain pending. No remote action or GPU use.

Step 1: fixture regressions pass; BF16_CACHE_GRADIENT_PARITY remains blocked at its original tolerance. Evidence: `work/build8/proofs/regressions/DISPOSITION.json` and `BF16_PARITY.json`.

Step 2: both inherited R2 failures pass in `work/build8/proofs/regressions/results.json`. The broader R2 check is pending in `work/build8/proofs/r2/`; its running source modules remain unchanged. Step 3: preparing CPU proofs for the inherited statement gaps.

Step 2: R2 passes 362 executions with no failures or errors (`work/build8/proofs/r2/results.json`).

Step 3: Native CPU producer/reader proofs are retained in proofs/cpu, proofs/cpu_fix and proofs/legacy_cpu. Remaining direct-source branches are exercised with item 7. Whole-file source hashes invalidate old cache and faithful-helper hits; the frozen suite will refresh coverage before the final gap count.

Step 4: The one local attempt failed before rank launch because the sandbox refused socket creation. This is not a pass. Lane runs proofs/stop_multirank/RUN.sh after build 8; RESULT.json records the failure and SOURCE.json states the CPU trap-chain scope.

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
