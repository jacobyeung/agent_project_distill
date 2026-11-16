The r4 packet is ready for review. It preserves OFF byte parity, restores the sensor provider, and audits structured point programs and all routed POOL types.

- 157 tests pass on both applied trees; 33 mutations are killed. [Tests](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R4.json), [mutations](/scratch/jjyeung/orch_n30/contracts_rebuild/out/MUTATION_R4.json).
- 360 rows per arm pass parity and ON admission checks. [Row families](/scratch/jjyeung/orch_n30/contracts_rebuild/out/ROW_FAMILY_PARITY_R4.json).
- 195564 POOL source records have 0 audit deferrals. [Audit](/scratch/jjyeung/orch_n30/contracts_rebuild/out/REAL_ROW_AUDIT_R4.json).
- 152 real captures have 0 failed replay assertions. [Replay](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay_r4/REAL_GEOMETRY_REPLAY.json).
- Patches apply cleanly to the sealed base and integration snapshot. [Apply proof](/scratch/jjyeung/orch_n30/contracts_rebuild/out/APPLY_PROOF_R4.json).
- Lane storage is 2658065396 bytes, below the 3000000000-byte cap; full tree copies total 4. [Integrity](/scratch/jjyeung/orch_n30/contracts_rebuild/out/PACKET_INTEGRITY_R4.json).

The full camera-pool and surface-converter wrappers still require their source authority packages. No GPU or model-quality claim is made. [Current contract and limits](/scratch/jjyeung/orch_n30/contracts_rebuild/out/CONTRACTS_REPORT_R4.md).
