# Packet suite support files (added by the operator, 2026-11-16 10:55Z)
The packet tests resolve `L = Path(__file__).resolve().parents[2]` and read support files under `L/work/...` and `L/out/...`.
`packet_root/` reproduces the contracts_rebuild layout for those files, copied byte for byte from /scratch/jjyeung/orch_n30/contracts_rebuild:
work/test_artifacts_r6, work/row_families_r4, work/row_families_r5, work/row_families_r6, work/ref, work/review2_inputs,
work/generator_baseline_r5.json, out/REAL_ROW_DEFECT_B1.json, work/base/work/base/tree_b01ce449, work/tests_r6 (identical to ../tests_r6),
work/run_tests_r6.py, work/final_suites_r6.py.
Run the packet suite from `packet_root/work/tests_r6` (so L = packet_root) with `R4_OVERLAY` pointing at the integrated tree.
Real-row fixtures named by absolute path inside tests_r6/real_*_r4.json (contracts_rebuild/work/real/x/*.jsonl.gz) stay where they are; read them in place.
