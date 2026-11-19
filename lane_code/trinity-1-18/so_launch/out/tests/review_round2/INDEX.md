# Review round 2 regression evidence

The saved reviewed production files match the exact prior combined tree byte for byte; the final artifact audit checks that identity. `work/replay_round2_before.py` copies those files into retained local scratch and runs the final new regression tests against them. The five delivery contracts instead read the saved reviewed documents/test files. Expected failures exit 1; the replay driver exits 0 only when it reproduces them.

| Check | Exact result | Output |
|---|---|---|
| Before: design/claims/coverage/patch order | `Ran 5 tests in 0.019s`; `FAILED (failures=5)` | [exact output](delivery.before.txt) |
| After: same contracts | `Ran 5 tests in 0.017s`; `OK` | [exact output](delivery.after.txt) |
| Before: receipt/CLI | `Ran 2 tests in 0.133s`; `FAILED (failures=2)` | [exact output](cache.before.txt) |
| After: full cache suite | `Ran 33 tests in 1.191s`; `OK` | [exact output](cache.after.txt) |
| Before: inherited lock contention | `Ran 1 test in 1.326s`; `FAILED (failures=2)` | [exact output](lock.before.txt) |
| After: full wrapper suite | `Ran 9 tests in 3.779s`; `OK` | [exact output](lock.after.txt) |
| After: real staging timing suite | `Ran 7 tests in 1.628s`; `OK` | [exact output](timing.after.txt) |
| After: earlier delivery contracts | `Ran 6 tests in 0.008s`; `OK` | [exact output](round1_contracts.after.txt) |

The real stage-lock implementation passes its new runtime test on the reviewed implementation too. Finding 4's failing regression is the missing-coverage contract, not an invented runtime bug. Timing OFF is compared with the real input `c.sh` using deterministic host/time stubs; both prep and preflight run under `bash -euo pipefail`.

Finding 1's documentation test does not replace the Orchard measurement. That measurement remains unavailable and unrun, as stated in the [report](../../REPORT.md) and [operator procedure](../../MEASURE_NATIVE_REUSE.md). Finding 2 tests the design requirements only; so_xstore implements the store.

All exact reproduction commands use the CPU environment in [commands.txt](../20261119T094926Z/commands.txt). Final standalone/recommended/combined tests and native baselines are in [the final verification directory](../20261119T094926Z/summary.json). The 92-test input/combined runs have the same five known fixture failures. [Extra probes](../20261119T094926Z/review_extra_probes.txt) cover chmod, concurrent write, symlink fallback, bounded frame tasks and randomized verdict/count parity. [Phase evidence](../20261119T094926Z/phase_evidence_check.txt) checks all 26 timestamp rows.

Retained diagnostics: [socket-limited attempt](socket_gate_attempt.txt), [cache schema fixture compatibility](cache.fixture_update.txt), and [case-sensitive wording contract](round1_contracts.wording_trial.txt). These are not successful test runs. Final logs above retain the passing suites. The blocked Gloo class is explicitly skipped in the final supported gate; no socket-dependent test is counted as passed.

[Final artifact audit](../final_artifact_audit.txt) checks hashes, base/result pins, each shell's syntax, Python syntax, test counts, document links, clean candidate inventories and the 3 GB workspace bound. The [hand-over note](../../NOTE_FOR_TREE_REBUILD.md) specifies application and enablement order. Patch 01 stays OFF.
