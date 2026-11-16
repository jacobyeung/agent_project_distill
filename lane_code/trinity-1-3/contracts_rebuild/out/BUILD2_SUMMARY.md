# Build 2 summary

The patch packet applies cleanly to the sealed base and the integration snapshot. The real-row audit and candidate-membership check pass. Sources: [APPLY_PROOF.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/APPLY_PROOF.json), [REAL_ROW_AUDIT.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/REAL_ROW_AUDIT.json), [REAL_CANDIDATE_UNIVERSE.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/REAL_CANDIDATE_UNIVERSE.json).

- The final candidates patch fixes demonstrated missing-manifest false positives and unit text in parsed object names. The patch, manifest and dependent final proofs are regenerated. Evidence: [REAL_ROW_DEFECT_B1.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/REAL_ROW_DEFECT_B1.json), [PATCH_MANIFEST.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/PATCH_MANIFEST.json).
- All 13001 distance and 1083 room programs pass admission in both source representations. Eligible pool counts are 11728 and 997; actual optimizer membership is unavailable. Source: [REAL_ROW_AUDIT.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/REAL_ROW_AUDIT.json).
- All 13001 distance rows agree with runtime membership. The sealed per-question universe would reject 17062 eligible operand occurrences; 17060 of 23456 fall outside its eight keys. Source: [REAL_CANDIDATE_UNIVERSE.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/REAL_CANDIDATE_UNIVERSE.json).
- The fixture proof covers 33 orientation cases in both epochs. All 11 inverted copies refuse; all 11 rolled copies pass. Exact-vertical lifting and MDG repair remain explicit parity exceptions. Source: [CPU_PROOF_B2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/CPU_PROOF_B2.json).
- Contract-suite outcomes: {'passed': 82}. Tree-suite outcomes: {'passed': 8, 'failed': 14}; unavailable record fixtures explain its failures. Source: [FINAL_TEST_RESULTS_B2.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_B2.json).
- Coverage: geometry 204/204; candidates 248/248; box 9/9; geometry_on_tree_r1 204/204. Source: [CHANGED_LINE_COVERAGE_B2.md](/scratch/jjyeung/orch_n30/contracts_rebuild/out/CHANGED_LINE_COVERAGE_B2.md).
- Rehearsal seal: `56c095a3cae04a71e03ca8e085da1911ade9e98e6859abd801a113a7e053df80`. Source: [INTEGRATION_SEAL.json](/scratch/jjyeung/orch_n30/contracts_rebuild/out/INTEGRATION_SEAL.json).

Apply with [apply_contract_patches.sh](/scratch/jjyeung/orch_n30/contracts_rebuild/out/apply_contract_patches.sh); start with `--dry-run`. The only rebase is [PATCH_geometry_on_tree_r1.diff](/scratch/jjyeung/orch_n30/contracts_rebuild/out/PATCH_geometry_on_tree_r1.diff). The script requires the hash helper, manifest and patches beside it.

Real capture recovery remains a records-derived prediction until `geometry_8c58df1547371bdb` arrives. The planned CPU replay is specified in [CONTRACTS_REPORT.md](/scratch/jjyeung/orch_n30/contracts_rebuild/out/CONTRACTS_REPORT.md). Retained test trees and staging are listed in [/scratch/jjyeung/orch_n30/contracts_rebuild/REMOVAL_CANDIDATES.md](/scratch/jjyeung/orch_n30/contracts_rebuild/REMOVAL_CANDIDATES.md).

Reader-facing text retains the sealed-versus-patched comparison because it defines replay behavior, and retains the defect/fix disclosure because the dispatch requires it.
