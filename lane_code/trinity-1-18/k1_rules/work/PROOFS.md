This file replaces the lost original out/PROOFS.md (written by kit_k1a/work/finalize.py:111 on trinity-2-18; no copy or hash survives). Lines 2 onward follow finalize.py:106-111 verbatim; proof statuses and P2 numbers came from out/<proof>_RESULT.json files that are lost and are marked [NOT RECOVERED]. No proof was rerun for this file.
CPU proof status. All paths below are relative to this lane. Real GPU parity, learned K1 accuracy, media staging, and production training admission are not measured.

| Proof | Status | Evidence |
|---|---|---|
| P1 | [NOT RECOVERED: out/P1_RESULT.json status] | out/P1_RESULT.json; out/P1_COVERAGE.json |
| P2 | [NOT RECOVERED: out/P2_RESULT.json status] | out/P2_RESULT.json; out/P2_LINE_HITS.json |
| P3 | [NOT RECOVERED: out/P3_RESULT.json status] | out/P3_RESULT.json; out/P3_COVERAGE.json |
| P4 | [NOT RECOVERED: out/P4_RESULT.json status] | out/P4_RESULT.json; out/P4_COVERAGE.json |
| P5 | [NOT RECOVERED: out/P5_RESULT.json status] | out/P5_RESULT.json; out/P5_COVERAGE.json |
| P6 | [NOT RECOVERED: out/P6_RESULT.json status] | out/P6_RESULT.json; out/P6_COVERAGE.json |
| P7 | [NOT RECOVERED: out/P7_RESULT.json status] | out/P7_RESULT.json; out/P7_COVERAGE.json |
| KIT | [NOT RECOVERED: out/KIT_RESULT.json status] | out/KIT_RESULT.json; out/KIT_COVERAGE.json |
| HANDOFF | [NOT RECOVERED: out/HANDOFF_RESULT.json status] | out/HANDOFF_RESULT.json; out/HANDOFF_COVERAGE.json |

P2 uses [NOT RECOVERED: p2['interpreter']], Python [NOT RECOVERED: p2['python']], NumPy [NOT RECOVERED: p2['numpy']], and scikit-learn [NOT RECOVERED: p2['sklearn']]. The maximum absolute coefficient/scaler/intercept difference is [NOT RECOVERED: p2['largest_difference']] (out/P2_RESULT.json). No fixture fit model is deployed.

P3 executes the shared frozen pricing comparator on real read-only dev-S1 proposals and geometry. It compares unrounded prices and errors exactly; it does not assert that the native printed response equals an unrounded old price. The native renderer is exercised separately by P4 and KIT. The dev-S1 fixture never enters a training fit.

P4 executes the reused o3_cache producer through real geometry conversion, proposal processing, selection and runtime calls, with stand-ins only at neural boundaries. Mutation checks reject GT response injection and refusal-ending fallback. Response spans include delimiters and carry zero loss. HANDOFF excludes failures without reviewed visual fallback evidence.

P5 runs the actual refit/export path on labelled synthetic feature rows from the fixed eligible room split. It rejects extra label-derived feature columns and benchmark captures. The result is marked fixture_only. Learned metrics on real K1 candidates remain unmeasured.

P6 runs the actual SAM tower encode/detect path with a CPU neural stub and recorded raw-prompt cache entry. It rejects a shifted frame, swapped phrase, and 0.05 score drift. It makes no real GPU parity claim.

P7 runs rs_tree Admission.check with real synthetic PNGs and sealed fixture membership on trust/fallback rows. out/FIRST_BATCH_CLI_RESULT.json verifies the handoff command. Production membership, provenance review, and tokenizer-level distributed first batches still belong to rs_tree.

Coverage files record executed lines, AST statement lines and missing statements. P2 records exact line hits in the unchanged source files. GPU-only and unexecuted branches remain visible; coverage is not represented as complete.

Logs: out/P1.log, out/P2.log, out/P3.log, out/P4_P7.log, out/P5.log, out/P6.log, out/KIT.log, out/HANDOFF.log.
