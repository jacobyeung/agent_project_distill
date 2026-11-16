# Current build state

The first full packaged qualification is running in exec session `93172`, launched through `qualify.py`. Its generator group completed; its legacy group is running. Read progress at most once per minute with `live_comparison.py`. Do not start another test suite while it runs: the harness compacts shared temporary products. Do not stop or rerun a killed job.

The packet suite passed every supplied test; evidence is `proofs/packet/results.json`. Complete canonical row-byte and target-byte parity passed for all supplied final A0 slices; evidence is `proofs/rows/PARITY.json`. The main source now has small changes beyond the packaged snapshot, so final kits, seal, packet and package qualification must be refreshed.

Main-tree fixture adaptations pending final verification:

- `tests/test_r2_build3.py`: the missing-vocabulary negative case supplies the required init identity and asserts the exact witness error. It previously passed on the earlier missing-init error, leaving its intended branch unchecked. The focused wrapper includes this method.
- `tests/test_r2_build6.py`: each below-threshold family fixture also passes through the pinned-receipt reader used by the launch entry, proving the actual read-side refusal before any worker call.
- `generator/derivgen_v7/test_v312_quality.py`: qualified-name refusal checks both OFF (old reason) and ON (accepted earlier exact-name refusal).
- `tests/test_c1_validation_slice.py`: retains the raw-config nonmutation check and checks the heading threshold's inclusion in identity.
- `tests/test_gxp_mix.py`: the memory-fallback fixture retains its legacy raw-configuration and FP32-output hashes, checks the ON identity with the accepted default heading threshold, and checks explicit OFF identities with and without that threshold. The first packaged diagnostic exposed this additional stale identity assertion.
- `launch_s1/b/i.py`: the standalone launch gate must mirror the accepted heading-threshold identity rule before private training modules are staged. The native-parity assertion in `test_s1_launch_kit.py` remains and now covers ON/OFF and invalid thresholds. This is a production integration fix, not a fixture expectation change; it is included in the focused wrapper.
- `student_pilot/r2_contract.py` and `tests/test_r2_build6.py`: the numeric and qualitative room-answer rules share the reader's room-alias list. Room rows compare their answer unit with the asked area unit, so a linear-foot label cannot pass a square-foot question. The new negative fixture checks that mismatch for every recognized room alias.
- `student_pilot/r2_units.py` and `student_pilot/r2_policy.py`: metric scores use ordered per-unit rows, since the native JSON writer sorts dictionary keys. The reader requires metres-first order, finite observed scores and explicit empty groups. The Build6 test round-trips through the actual writer/reader; its policy fixture uses the same representation. These changes await focused and final validation.

Required next steps:

The comparison now requires the same classified cause in the tree and untouched base before calling a legacy failure pre-existing. Inspect any different-cause events rather than treating every shared failing test name as sufficient.

1. Let the running package finish. Inspect `LIVE_B5_LOSSES.json`, run `compare.py`, and resolve every actual lost pass. Preserve the first package receipts with `retain_suite_diagnostic.py` before overwriting the fixed suite outputs.
2. The audited census comparison passed with identical values and no meaningful speed difference (`proofs/census/EQUIVALENCE.json`). Keep `R2_FAST_CENSUS=0`; do not repeat the benchmark. It only read the temporary tree and did not compact or change it.
3. Run `bash work/build6/TARGETED_TEST.sh` after the package finishes. Its driver runs the current Build6 tests, the repaired legacy fixtures and `coverage_cases` through `test_runner.py` into `proofs/final_targeted`. The edge fixture supplies a nested binding, an explicit tool-error response and a qualitative trace with a final answer. The final package includes the wrapper, driver and supplemental module. Keep tests sequential.
4. After source changes stop, use `restage_kits.py` (retains previous kits under their old seal), then run the final packet suite and `qualify.py`. The latter now also measures temporary bytes around each proof, runs strengthened baseline/current row proofs and the empty-directory delivery harness. Source edits during native preparation cause legitimate source-closure failures; keep the tested snapshot stable.

The final package wrapper now records unpacked bytes from the actual archive-member inventory, rather than its preliminary member list. This receipt correction and the fresh empty extraction directory are pending the final package run.
5. Run `coverage_all.py`; inspect `GAPS.json`, add meaningful external proof tests for CPU gaps, and classify only real external-input boundaries. Preserve exact-current-file and compiled-code filtering. Additional proof scripts can live outside the sealed tree to avoid restaging when production source is unchanged.

Coverage now includes edits on continuation lines of simple statements and compound-statement headers. It still requires a directly observed head line and both fingerprints; it does not infer execution from a child statement. The final denominator may therefore exceed the preliminary count.
6. Run `integration_check.py`, `record_gate_fix.py`, `record_adaptations.py`, `kit_readcheck.py`, `static_audit.py`, `final_verify.py`, `report.py`, and `finish_docs.py` once final evidence exists. `record_gate_fix.py` must bind the passing focused native-parity test to the current gate and test hashes. It records the extra per-hunk repair in `out/CONTRACTS_INTEGRATION.md`. Review generated reports for accuracy. `report.py` writes the final report/status; `finish_docs.py` refreshes the card and appends the requested design section.

The integration has unchanged exact packet bytes and accounted-for merges (`INTEGRATION_CHECK.json`, `INTEGRATION.json`). Both level-basis functions are unchanged. Protected artifact modes and the grammar/exclusion hashes pass the static audit. The source has no fixed init constant; the explicit fallback selection and fixture pin are in `out/INIT_INPUT.json` and `fixtures/work/build6/INIT_INPUT.json`. No tested newer export was supplied. The generic archive reader accepts the pinned export layout. All evidence obligations remain, and both kit authorizations are closed.

The packet's supporting inputs are available under `work/contracts_r6/packet_root`; `packet_inputs.py` staged only the required text fixtures into the fixed packet proof folder. Do not claim those inputs are missing. The historical full RGB/scene-intake receipts remain absent; packed-row parity does not qualify those joins. The report must say this explicitly.

The present delivery record is `DELIVERY.json`; it describes the running diagnostic snapshot, not the latest working-tree edits. The final report is still pending. No launch, remote call, GPU or other agent is authorized.
