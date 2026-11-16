# Build 3 status

Review artifacts are delivered. The updated tree and pristine A0/A2 kits share the verified seal in `out/TREE_SEAL.json` and `out/B3_KITS.json`. The reports are `out/BUILD3_REPORT.md`, `out/FRAME_HOST_JOB.md` and `out/PRELAUNCH_CARD.md`; the design record has its Build 3 section. No launch, remote work or GPU work ran.

The combined regression suite passed 136 tests (`out/B3_ALL_TEST_RESULTS.json`). Closing, gap and final suites passed 19, 12 and 5 tests respectively (`out/B3_CLOSURE_TEST_RESULTS.json`; `out/B3_GAPS_TEST_RESULTS.json`; `out/B3_FINAL_TEST_RESULTS.json`). The direct trace-callback test passed (`out/B3_TRACE_FIXED_TEST_RESULTS.json`). The report records earlier failures and their fixes.

Changed-statement coverage is 4358/4370 overall and 2592/2604 in production code. No CPU-reachable statement remains unexecuted; the remaining 10 frame-host and 2 GPU statements have explicit classifications (`out/B3_COVERAGE_CLASSIFIED.json`).

Both actual `job.sh` entries staged from empty proof folders and refused at `Missing component evidence: init_m544`. No model stand-in was reached in those entry proofs. The integrated native producer/readers and tiny native loader/parity proofs are separate, with their substitutions stated (`out/B3_FRESH_ENTRY_PROOF.json`; `out/B3_NATIVE_JOB_PROOF.json`; `out/B3_LOADER_PROOF.json`; `out/B2_MODEL_PROOF.json`).

The host job remains unrun. It needs real input pins, runtime/path validation and independent admission. The parent shell/staging workflow is not unchanged end to end. Native source namespaces and runtime receipt contents remain outside the external naming scan; the report identifies this limitation explicitly. These limits prevent unconditional launch signoff.

The named contract and row-slice folders remain absent (`out/B3_INPUT_AVAILABILITY.json`). The deferred contract script is `work/build3/APPLY_CONTRACT_PATCHES.sh`. No real-row success or real after-filter repeat table is claimed.

The real producer wrote 10,248,192 SQLite bytes for 2,000 synthetic rows; the extrapolation uses an explicitly hypothetical population (`out/B3_ESTIMATOR_PROOF.json`). Temporary files measured 186,161,340 bytes against 200,000,000; the lane measured 707,206,770 bytes against 2,000,000,000 (`out/B3_FINAL_REVIEW.json`).

Defaults: keep opener rows only after verified lineage/vocabulary checks; retain the parent archive convention; refuse unsupported banks and missing real evidence; require separate host admission and GO. Process deviations, including the deliberately interrupted duplicate test invocation and the startup skill read, are recorded in `out/BUILD3_REPORT.md`.
