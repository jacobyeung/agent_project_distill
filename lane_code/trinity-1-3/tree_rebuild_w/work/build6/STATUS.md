# Build 6 status

The first packaged diagnostic is running. The working tree contains additional repairs that still require focused and final packaged verification. The current delivery record describes the diagnostic snapshot, not the final source.

| Completed group | Run | Passed | Error / failure events | Source |
|---|---:|---:|---:|---|
| tree / generator | 32 | 18 | 16 / 1 | `work/build6/proofs/suite_tree/generator/results.json` |
| tree / legacy | 1810 | 1280 | 444 / 17 | `work/build6/proofs/suite_tree/legacy/results.json` |

The exact contract hashes and unchanged level-basis functions pass (`work/build6/INTEGRATION_CHECK.json`). Packet and packed-row receipts are in `work/build6/proofs/packet/results.json` and `work/build6/proofs/rows/PARITY.json`.

Final coverage remains provisional. Legacy failures require matching causes in the untouched base; the entire R2/shared-grammar group must pass. Pending repairs and the remaining workflow are recorded in `work/build6/RESUME.md`. No launch is authorized.
