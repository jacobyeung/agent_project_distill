# Build 6 status

The first packaged diagnostic is running. The working tree contains additional repairs that still require focused and final packaged verification. The current delivery record describes the diagnostic snapshot, not the final source.

| Completed group | Run | Passed | Error / failure events | Source |
|---|---:|---:|---:|---|
| tree / generator | 32 | 18 | 16 / 1 | `work/build6/proofs/suite_tree/generator/results.json` |
| tree / legacy | 1810 | 1280 | 444 / 17 | `work/build6/proofs/suite_tree/legacy/results.json` |
| tree / r2 | 349 | 349 | 0 / 0 | `work/build6/proofs/suite_tree/r2/results.json` |
| base / generator | 14 | 1 | 16 / 0 | `work/build6/proofs/suite_base/generator/results.json` |
| base / legacy | 385 | 3 | 444 / 14 | `work/build6/proofs/suite_base/legacy/results.json` |
| base / r2 | 0 | 0 | 0 / 0 | `work/build6/proofs/suite_base/r2/results.json` |

The exact contract hashes and unchanged level-basis functions pass (`work/build6/INTEGRATION_CHECK.json`). Packet and packed-row receipts are in `work/build6/proofs/packet/results.json` and `work/build6/proofs/rows/PARITY.json`.

Final coverage remains provisional. Legacy failures require matching causes in the untouched base; the entire R2/shared-grammar group must pass. Pending repairs and the remaining workflow are recorded in `work/build6/RESUME.md`. No launch is authorized.
