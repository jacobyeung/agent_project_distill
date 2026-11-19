from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build16'
(B/'STATUS.md').write_text('''# Build 16 status

GO=false.

| Step | Status | Evidence |
|---|---|---|
| 1 | Inputs/card bound; complete K1 authority absent | INPUTS.json; inputs/; proofs/census/CENSUS.json |
| 2 | Procedure guard and 17,879-row classifier comparison pass | proofs/census/CLASSIFIER.json; proofs/final_focused/TESTS.json |
| 3 | Real census, 1,000-step and resumed plans pass; camera/pose/pointing host counts are labelled substitutes | proofs/census/PLAN_RUN.json; proofs/traces/INDEX.json |
| 4 | Separate q mode and operator packet implemented; full native chain fixture and real host admission unqualified | proofs/operator/OPERATOR.md; proofs/final_focused/b16/persisted_400/FORWARD.json |
| 5 | Persisted metadata reader and native export init pass for synthetic 400/600 exports; real P export absent | proofs/final_focused/b16/persisted_400/RESULT.json; proofs/operator/P_PRODUCER_EQUALITY.json |
| 6 | Frozen packet exact float assertion is test-only; runtime content hashes retain pinned-value identity | proofs/float/RESULT.json |
| 7 | Fresh kits staged GO=false; final suites, mutations, coverage and package in progress | KIT_RESULT.json |
''')
