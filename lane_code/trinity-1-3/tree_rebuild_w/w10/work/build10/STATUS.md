# Build 10 status

GO=false. Source: STEPS.json.

- G8: BLOCKED_PTRACE. All executable harness tests and the focused fixed_math contract pass. The original syscall-witness denial remains. Evidence: proofs/g8_available/RESULT.json; proofs/g8/test.log; HARNESS_COVERAGE.json.
- G1: PARTIAL_BLOCKED. Registered readout passes available numeric parity. Point-depth helpers, public transforms and legacy branches remain; bound producer operands are missing. Evidence: EAT1_GROUP_EVIDENCE.json; proofs/parity/BYTE_PARITY.json.
- G2: BLOCKED_ACCEPTANCE. Serving degree readout and available-input parity pass. The scanner flags the legacy branch; bound raw poses are missing. Evidence: proofs/parity_build7/RESULT.json; EAT1_GROUP_EVIDENCE.json.
- G3: BLOCKED_BOUND_INPUTS. Artifact threshold and availability tests pass. Bound producer rotations are missing. Evidence: proofs/g3/RESULT.json; proofs/parity/NESTED_OPERANDS.json.
- G4: PARTIAL. Frame-count and readout configuration are exported. Shared standalone calculator compatibility and all frame-64 readers remain unqualified. Evidence: proofs/g4/RESULT.json.
- G5: IMPLEMENTED. Artifact budgets refuse overlong calls, excess calls and incomplete response injection. Evidence: proofs/g5/RESULT.json.
- G6: IMPLEMENTED_CLAUSE_BLOCKED. Production and GF-1 tiny manifests bind preprocessing and vendor sources as tower files. Harness v7 still reports executed helper constants; no file-role exemption or suppression was added. Evidence: proofs/g6/RESULT.json; eat1/adapters/build10_manifest.py; EAT1_GROUP_EVIDENCE.json.
- G7: PARTIAL. Out-of-range calls refuse without tokens. Ground dispatch is named ground_route. Status literals lacking an owning head output remain A4 blockers; no suppression added. Evidence: proofs/g7/RESULT.json.
- FINAL: BLOCKED. Source, kits, final archive, packet suite, frozen comparison, final readers and coverage are recorded. Admission remains false. See ../../out/BUILD10_REPORT.md and FINAL_PASS.json.
- PARITY: BLOCKED_BOUND_INPUTS. Build 7 original reader weights and frames reproduce every available numeric response byte-for-byte. Bound slices lack nested raw geometry operands. Evidence: proofs/parity_build7/RESULT.json; proofs/parity/NESTED_OPERANDS.json; proofs/parity/BYTE_PARITY.json.
- EAT1: BLOCKED. Final GF-1, C8r and b04 judgments are FAIL, claim_grade=false. B04 A2 PASS covers an early-failing path: six tool-bearing items refuse sealed_validate_mismatch. Evidence: EAT1_SUMMARY.json and proofs/eat1/*/run/ITEMS.jsonl.
