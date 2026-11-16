# Current build state

The first full packaged qualification is running in exec session `93172`, launched through `qualify.py`. Its generator group completed; its legacy group is running. Read progress at most once per minute with `live_comparison.py`. Do not start another test suite while it runs: the harness compacts shared temporary products. Do not stop or rerun a killed job.

The packet suite passed every supplied test; evidence is `proofs/packet/results.json`. Complete canonical row-byte and target-byte parity passed for all supplied final A0 slices; evidence is `proofs/rows/PARITY.json`. The main source now has small changes beyond the packaged snapshot, so final kits, seal, packet and package qualification must be refreshed.

Main-tree fixture adaptations pending final verification:

- `generator/derivgen_v7/test_v312_quality.py`: qualified-name refusal checks both OFF (old reason) and ON (accepted earlier exact-name refusal).
- `tests/test_c1_validation_slice.py`: retains the raw-config nonmutation check and checks the heading threshold's inclusion in identity.
- `student_pilot/r2_contract.py` and `tests/test_r2_build6.py`: the numeric room-answer rule covers both room type aliases. Room rows also compare their answer unit with the asked area unit, so a linear-foot label cannot pass a square-foot question. The new negative fixture checks that mismatch.

Required next steps:

1. Let the running package finish. Inspect `LIVE_B5_LOSSES.json`, run `compare.py`, and resolve every actual lost pass. Preserve the first package receipts with `retain_suite_diagnostic.py` before overwriting the fixed suite outputs.
2. The audited census comparison passed with identical values and no meaningful speed difference (`proofs/census/EQUIVALENCE.json`). Keep `R2_FAST_CENSUS=0`; do not repeat the benchmark. It only read the temporary tree and did not compact or change it.
3. Run targeted current-tree tests and `coverage_cases` through `test_runner.py` into fixed proof folders. The latter covers contract edge cases found by the preliminary coverage audit. Its dictionary-binding fixture now supplies a nested binding, an explicit tool-error response and a final answer. `make_delivery.py` includes this supplemental test module. Run tests sequentially; use `run.sh` for environment and file limits. Test imports can find `coverage_cases.py` via the harness directory.
4. After source changes stop, use `restage_kits.py` (retains previous kits under their old seal), then run the final packet suite and `qualify.py`. The latter now also measures temporary bytes around each proof, runs strengthened baseline/current row proofs and the empty-directory delivery harness. Source edits during native preparation cause legitimate source-closure failures; keep the tested snapshot stable.
5. Run `coverage_all.py`; inspect `GAPS.json`, add meaningful external proof tests for CPU gaps, and classify only real external-input boundaries. Preserve exact-current-file and compiled-code filtering. Additional proof scripts can live outside the sealed tree to avoid restaging when production source is unchanged.
6. Run `integration_check.py`, `record_adaptations.py`, `kit_readcheck.py`, `static_audit.py`, `final_verify.py`, `report.py`, and `finish_docs.py` once final evidence exists. Review generated reports for accuracy. `report.py` writes the final report/status; `finish_docs.py` refreshes the card and appends the requested design section.

The integration has unchanged exact packet bytes and accounted-for merges (`INTEGRATION_CHECK.json`, `INTEGRATION.json`). Both level-basis functions are unchanged. Protected artifact modes and the grammar/exclusion hashes pass the static audit. The source has no fixed init constant; the explicit fallback selection and fixture pin are in `out/INIT_INPUT.json` and `fixtures/work/build6/INIT_INPUT.json`. No tested newer export was supplied. The generic archive reader accepts the pinned export layout. All evidence obligations remain, and both kit authorizations are closed.

The packet's supporting inputs are available under `work/contracts_r6/packet_root`; `packet_inputs.py` staged only the required text fixtures into the fixed packet proof folder. Do not claim those inputs are missing. The historical full RGB/scene-intake receipts remain absent; packed-row parity does not qualify those joins. The report must say this explicitly.

The present delivery record is `DELIVERY.json`; it describes the running diagnostic snapshot, not the latest working-tree edits. The final report is still pending. No launch, remote call, GPU or other agent is authorized.
