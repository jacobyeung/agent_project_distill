# Build 6 decisions

Use the original packet base for three-way integration. Preserve the existing level_basis function byte for byte. Keep simulated GT recovery admission with contracts OFF; require the packet training audit with contracts ON. These defaults preserve earlier behavior while adding the accepted contract.

The packet's supporting comparison fixtures are supplied under `work/contracts_r6/packet_root`. Use those exact text fixtures, retain every assertion, and adapt only paths and execution plumbing. Their staged hashes are in `work/build6/PACKET_INPUTS.json`.

No tested D0 export is supplied. The default init selection is the pinned step-544 fallback, recorded in `out/INIT_INPUT.json`; its missing admission evidence remains missing. A2 receives admission priority. A0 is its fallback, and neither kit is a control.

The full units census has no per-unit breakdown. Report the exact slice frequencies and total registered rows per step. Label any per-unit projection from those slice frequencies GUESS.

For persisted metric reports, the options are keyed values with separate ordering metadata or ordered per-unit rows. Use ordered rows by default: the native canonical JSON writer sorts dictionary keys but preserves list order. Empty unit groups carry a zero count and no score; observed groups require finite scores.

Legacy assertions that name an epoch-specific refusal run explicitly in both epochs: retain the exact old OFF expectation and add the accepted ON expectation. Do not broaden an assertion to accept either result or alter the packet's required exact files. Record these fixture adaptations in `work/build6/TEST_INPUT_ADAPTATIONS.json`.

For the legacy FP32 byte fixture, the options are changing expected hashes or explicitly restoring its original CPU reduction order. Use the original one-thread setting, restore the caller's setting afterward, and preserve every expected hash. The encoder source is unchanged and the diagnostic reproduces both thread-dependent results (`work/build6/proofs/tensor_threads/RESULTS.json`).

For legacy failure comparison, the options are matching failed test names or matching both names and classified causes. Use matching names and causes by default, retaining every error event per test. An explicit exception preserves unsupported-reader refusals when the same test also fails in the untouched base, its refusal matches the Build-5 receipt, and its guard sources remain authenticated (`work/build6/LEGACY_GUARDS.json`). Keep the different base cause visible. Other differing causes remain flagged for review in `work/build6/SUITE_COMPARISON.json`.

For room-runtime coverage, the options are testing the room-capable protocol selected by the kits or migrating the legacy protocol. Use the selected 3.14 protocol in every current session implementation; both staged kits already select it (`work/build6/KIT_PROTOCOLS.json`). The accepted exact files retain the legacy 3.13 refusal for room calls (`work/tree_r1/trace_format/ground_v313.py`, `work/tree_r1/student_pilot/live_trace313.py`). The final kit reader checks the selected protocol (`work/build6/kit_readcheck.py`).
