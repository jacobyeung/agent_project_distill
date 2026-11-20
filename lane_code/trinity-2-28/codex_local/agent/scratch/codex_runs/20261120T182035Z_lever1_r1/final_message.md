Built and CPU-tested; nothing submitted.

- **Forecast:** 16.75 worker minutes; 28.75 including staging/transfers. Return: approximately **40 MB compressed**, capped at 1 GB.
- **Files:** [builder](/scratch/jjyeung/orch_n30/lever1_c/r1/build_depth.py), [package](/scratch/jjyeung/orch_n30/lever1_c/r1/out/delivery.tgz), [placement commands](/scratch/jjyeung/orch_n30/lever1_c/r1/PLACE.md), [seven-cell relift harness](/scratch/jjyeung/orch_n30/lever1_c/r1/relift.py).
- **Validation:** 14 tests passed; 20 real T1 gaps reproduced exactly; stub entry and import checks passed. Dry run reports `depth return missing`.
- **Deviations:** inherited guard requires a 40-minute allocation. GT binding and portrait censoring leave **56 items / 28 captures**. Float16 depth includes a lossless residual.

No gain verdict yet: the return must pass the **0.00 m parity gate**. [Full report](/scratch/jjyeung/orch_n30/lever1_c/r1/REPORT.md).