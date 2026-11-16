The r3 packet is ready for independent review. It fixes partial-ground recovery, generator class dispatch, cache binding, status parsing, malformed-row handling, normalization, and application preflight. Source: [REVIEW_DISPOSITION_R3.md](/scratch/jjyeung/orch_n30/contracts_rebuild/out/REVIEW_DISPOSITION_R3.md).

The installed-tree checks pass 140 tests; all 25 tested mutations are killed, including every reviewed survivor. Sources: [FINAL_TEST_RESULTS_R3.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R3.json), [MUTATION_R3.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/MUTATION_R3.json).

The replay covers 152 captures with 0 failed assertions and exact OFF/base parity. Source: [real_replay_r3/REAL_GEOMETRY_REPLAY.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay_r3/REAL_GEOMETRY_REPLAY.json).

Apply with [apply_contract_patches_r3.sh](/scratch/jjyeung/orch_n30/contracts_rebuild/out/apply_contract_patches_r3.sh). Application, read-only refusal, and reapplication proofs are in [APPLY_PROOF_R3.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/APPLY_PROOF_R3.json). The full report is [CONTRACTS_REPORT_R3.md](/scratch/jjyeung/orch_n30/contracts_rebuild/out/CONTRACTS_REPORT_R3.md).

The proof covers tool behavior and training rendering, not RGB-model accuracy. The gravity-noise evidence distinguishes heading instability from ordinary changes in vertical projection.
