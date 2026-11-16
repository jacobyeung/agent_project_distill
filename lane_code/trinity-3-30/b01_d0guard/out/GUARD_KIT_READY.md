# Guard-read kit for D0 exports: review-ready, not launch-ready

INTERNAL INSTRUMENT: every guard-read number is for choosing the next leg's init and is never a claimed result (the C8r backend has fitted parts the user ruled harness).

## Package (trinity-3-30 /scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build2/out/; index GUARD_KIT_READY.md there)
| Artifact | sha256 |
|---|---|
| code_g2.tar (C8r bytes unchanged + guard_kit modules; G3 seal) | 9ffa724919aa52adf94793a5f0a6912d867797d8aa55a179d2366282bc695bdc |
| inputs_g2.tar | 3be24165b9856024dc5359b1760a8a1ad88f11022972fb3d075edb70c02aff72 |
| FAMILY.json (refuses launch until review + closure + ORCH GO records exist) | 273d5d5661fc7fea166aa6603411c1db8e23c7a8e9bc8b7ae8f8c1044737029b |
| report guard_kit/report/guard_read.py | 6fead56128b2081314e52aa0ca6a7ab2f077aac72078554f2d1d7b61067aacc6 |
| D0 closure fixture m50 (read-only Orchard copy) work/d0closure/closure_359fcc3c.tar | 41bb90d0418ab37715ae66358e875cb4f337f7a63349df4d96498c6452cda964 |

## Review targets
DIFF.md (line-by-line source changes; G3_ADMISSION.patch), PIN_CLASSIFICATION.md (46 C8r checks: export-dependent vs export-independent with file:line), RESTORATION.md, NAMING.md, guard_read.py.

## Tests (all run; logs named)
- 134 unit/suite checks PASS, 25/25 report mutants killed (build2/out/TESTS.json, MUTANTS.json). guard_read.py: 27 tests, 25/25 mutants, self-pair on job 170056 zero differences (out/tests/, out/selftest/).
- D0 m50 real metadata: config identity 4bc5442c, preparation d898614a, source tree b01ce449, trained-group chain to m544, unchanged C8r restoration checks PASS (CLOSURE_ADMISSION.json, RESTORATION_TEST.json).
- Whole-worker CPU rehearsal outside the sandbox, production coordinator, tiny-model C8r boundary: rehearsal/whole/31f44f39c63b4d68be53660ff5780980/RESULT.json all ten steps (stage..report; report refuses the 20-item fixture rc 3 by design). Rerun on the final G3 seal (code_g2.tar 9ffa7249): rehearsal/whole/6bcb6c74a28545f48cb24a05517ca0c6/RESULT.json PASS_WITH_EXPECTED_REPORT_REFUSAL, same ten steps. Copies of these receipts: out/evidence/.
- Mismatch variant: rehearsal/whole/4883e36e095649de8e1ac446991273ae: PROOF FAIL at the first item, receipt published, no candidate phase (EXPECTED_REFUSAL).
- Not checked: real tensors, GPU parity, real token identity (the in-job proof does that), Orchard/GCS staging live, publication to the live pool.

## Time and disk
Job need ~3 h 25 min, limit 05:00:00, 1 H100 on general (SIZING.json); job disk ~250 GB on node-local storage. Kit on Trinity ~0.5 GB.

## Open for ORCH
- Naming: 7 member names inside sealed trainer tree b01ce449 (e.g. rk/revsi.py); renaming changes the verified tree hash; the same tree already ran in job 170056 and D0 job 170111. All new job-visible names are neutral (round-trip proof NAME_ROUNDTRIP.json).
- Per step: fetch m<STEP> closure read-only (RUN.md), the review, list sha in the init-rule record, ORCH GO naming the job.
