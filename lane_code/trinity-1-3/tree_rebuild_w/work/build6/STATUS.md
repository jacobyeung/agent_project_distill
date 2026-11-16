# Build 6 status

Final packaged qualification is running. The source remains frozen.

Active package group: `tree/legacy`; completed executions: 1378. Source: `work/build6/proofs/suite_tree/progress.json` and its group progress receipt.

Detected lost build-5 pass events: 0 (`work/build6/LIVE_B5_LOSSES.json`). This live check does not replace the final base comparison.

The packet suite passed on the final source (`work/build6/final_packet.log`). The focused repairs passed (`work/build6/proofs/final_targeted/results.json`). OFF/ON packed-row parity passed (`work/build6/proofs/rows/PARITY.json`).

The exact and merged contract files are verified (`work/build6/INTEGRATION_CHECK.json`). Both restaged kits passed their scan and read checks (`work/build6/kits/RESULTS.json`, `work/build6/KIT_READCHECK.json`). Delivery identity: `work/build6/DELIVERY.json`.

| Completed driver step | Return code | Log |
|---|---:|---|
| restage | 0 | `work/build6/final_restage.log` |
| kit_readcheck | 0 | `work/build6/final_kit_readcheck.log` |
| kit_protocols | 0 | `work/build6/final_kit_protocols.log` |
| packet | 0 | `work/build6/final_packet.log` |

Coverage remains provisional until the driver aggregates final receipts. Initial diagnostic evidence is retained under `work/build6/proofs/suite_tree/diagnostic_results.json` and the corresponding base proof.

Full RGB/scene admission and missing evidence records remain unqualified. Both kit authorizations stay closed. No launch is authorized. Remaining work is recorded in `work/build6/RESUME.md`.
