# Guard-read kit for D0 exports: review-ready, not launch-ready

INTERNAL INSTRUMENT: every guard-read number is for choosing the next leg's init and is never a claimed result (the C8r backend has fitted parts the user ruled harness).

## Package (trinity-3-30 /scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build2/out/; index GUARD_KIT_READY.md there)
| Artifact | sha256 |
|---|---|
| code_g2.tar (C8r bytes unchanged + guard_kit modules; G5 seal after review fixes) | 6024aa2be082b1881a8e33f52dcaa7d57c209858d6a1adf8d25bbb97516cb54e |
| inputs_g2.tar | 3be24165b9856024dc5359b1760a8a1ad88f11022972fb3d075edb70c02aff72 |
| FAMILY.json (refuses launch until review + closure + ORCH GO records exist) | 23cadfceac2896ab0f5f0ae7edc05cca64af7925277539beae321b784cf2f302 |
| report guard_kit/report/guard_read.py (after review fixes; pinned in worker.py) | 5424e41c68fc1918386c62865a68d7b3c1af2802f2800b1f0455837568a3cd11 |
| D0 closure fixture m50 (read-only Orchard copy) work/d0closure/closure_359fcc3c.tar | 41bb90d0418ab37715ae66358e875cb4f337f7a63349df4d96498c6452cda964 |

## Review targets
DIFF.md (line-by-line source changes; G3_ADMISSION.patch), PIN_CLASSIFICATION.md (46 C8r checks: export-dependent vs export-independent with file:line), RESTORATION.md, NAMING.md, guard_read.py.

## Tests (all run; logs named)
- 158 suite checks PASS, 31/31 report mutants killed (build2/out/TESTS.json, MUTANTS.json; G5). guard_read.py: 38 tests (out/tests/guard_read_tests_v5.log), 31/31 mutants (out/tests/guard_read_mutants_v6.json), self-pair on job 170056 (--self-pair) zero differences.
- Reviews: Codex Astra (report and merge) GO AFTER FIXES, then two confirmation rounds, all findings fixed (agent/scratch/codex_runs/*b01_review_guard_codex{,2,3}*). Devin Opus review_guard GO AFTER FIXES (events/review_guard/REVIEW_VERDICT_GUARD.md); fixes 1-4 done (report by me; DIFF vs C8r, return receipts, governed fetch by Codex G4/G5); confirmation running (briefs/review_guard_confirm.md).
- D0 m50 real metadata: config identity 4bc5442c, preparation d898614a, source tree b01ce449, trained-group chain to m544, unchanged C8r restoration checks PASS (CLOSURE_ADMISSION.json, RESTORATION_TEST.json).
- Whole-worker CPU rehearsal outside the sandbox, production coordinator, tiny-model C8r boundary: rehearsal/whole/31f44f39c63b4d68be53660ff5780980/RESULT.json all ten steps (stage..report; report refuses the 20-item fixture rc 3 by design). Rerun on the final G3 seal (code_g2.tar 9ffa7249): rehearsal/whole/6bcb6c74a28545f48cb24a05517ca0c6/RESULT.json PASS_WITH_EXPECTED_REPORT_REFUSAL, same ten steps. Copies of these receipts: out/evidence/. Final seal G5 (code_g2.tar 6024aa2b): rehearsal/whole/ffdbd8e316a04872a588fcb8eeabc96a/RESULT.json PASS_WITH_EXPECTED_REPORT_REFUSAL, all ten steps; report called with --candidate-artifact and refuses only for the 20-item fixture (616 items absent); the return carries CANDIDATE_STAGE.json, CHECK.json, STAGE_RECEIPTS.json and the step-544 export's CHECK.json (out/evidence/pass_g5_ffdbd8e3/).
- Mismatch variant: rehearsal/whole/4883e36e095649de8e1ac446991273ae: PROOF FAIL at the first item, receipt published, no candidate phase (EXPECTED_REFUSAL).
- Not checked: real tensors, GPU parity, real token identity (the in-job proof does that), Orchard/GCS staging live, publication to the live pool.

## Time and disk
Job need ~3 h 25 min, limit 05:00:00, 1 H100 on general (SIZING.json); job disk ~250 GB on node-local storage. Kit on Trinity ~0.5 GB.

## Open for ORCH
- Naming: ACCEPTED by ORCH 1601Z for the 7 member names inside sealed trainer tree b01ce449 (listed in distill_design/GUARD_READ_KIT_D0_20261116.md). All new job-visible names are neutral.
- The init rule still needs the distance list sha256 (028273ec…).
- Per step: fetch m<STEP> closure read-only (RUN.md), the review, list sha in the init-rule record, ORCH GO naming the job.
