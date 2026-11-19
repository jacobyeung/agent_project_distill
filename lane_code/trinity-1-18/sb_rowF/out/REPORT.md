sb_rowF builds 17,737 counting rows per alternative: B is the default; --form A emits tallies.
The kit is complete for review, but the required unchanged-N validation gate FAILS. No training admission is claimed.

The generator uses W/w19 sealed tree_r1, 8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa.
Store v7 matches 210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443 (204,413 rows).
The census finds 20,669 counting rows: 18,052 first-seen sources and 2,617 outside this scope.
All 18,052 sources convert mechanically; 17,737 pass the independent-annotation and room checks.
The source union includes all 17,879 z.json list rows and 173 additional lists already removed by n.json.
Of the converted rows, 17,564 come from z.json; 173 carry outside_native_training_division exclusions.
ADMISSION_SCOPE.json lists those 173 rows. New qids do not override their native-division exclusions.

| Source cell | Mechanical | Emitted per form | Refused |
|---|---:|---:|---:|
| b12_cntapp_gt_v1 / multiple | 8064 | 8064 | 0 |
| b12_cntapp_gt_v1 / single | 2113 | 2113 | 0 |
| r1g / single | 6636 | 6362 | 274 |
| rows_rebuild_d0_ARKIT_gaps / multiple | 363 | 341 | 22 |
| rows_rebuild_d0_T0_gaps / multiple | 290 | 282 | 8 |
| rows_rebuild_d0_T1H1_gaps / multiple | 307 | 300 | 7 |
| rows_rebuild_d0_T1H2_gaps / multiple | 279 | 275 | 4 |

REFUSALS.jsonl lists 315 refusals: 228 K1-held-out rooms, 84 MISSING independent instance annotations, and 3 MISSING canonical-room mappings.
Each missing-input refusal names its qid and the exact expected structured field or mapping key. No mapping or GT was invented.
REMOVE.json is empty JSONL in n.json format: every emitted source is already removed by n.json or z.json.
REMOVE_RECEIPT.json binds the empty file hash and the exact set difference.

| Truth | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10+ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rows per form | 0 | 22 | 5075 | 2471 | 3635 | 1877 | 1366 | 907 | 693 | 457 | 1234 |

Exact source and emitted cell counts are asserted against inputs/EXPECTED_CELLS.json; no cell is sampled or silently shortened.
Every source is used once per alternative. The two alternatives have disjoint qids and candidate_ids; kit formulas bind the new qid and unchanged question.
Full field diffs permit only qid, candidate_id, target, and provenance.sb_rowF. All 82,716 instance entries per form match independent annotated IDs and frames.
The independent audit verifies every row, region multiplicity, category sum, final answer, histogram, removal, and K1/R0/withheld-80/dev-S1/BENCH-v2 room exclusion.
All 18,052 original sources pass student-input, row-schema, native-direct, and shared-grammar validation.
All 17,737 new rows per form pass student-input, row-schema, and proposed-form validation; all FAIL unchanged N native-direct, shared-grammar, and counting admission.
N ground_rows.pack fails on all 18,052 sources and 17,737 new rows per form: these direct rows lack routed ground-record fields. CHECKS.json retains the failures.
Contract tests pass 12 positive cases and 33 malformed variants, including repeated/skipped ordinals, frame range/order, wrong totals, and region sums.
READ30.md prints 30 full rows per form. The assistant reviewed every selected question and complete trace against its annotations; independent checks compare all JSON fields.

New questions: 0. New trace bodies and individual lines are screened against 1,017 kit/fixture/R0-item wordings at normalized Levenshtein distance <=0.10; removed: 0 in each form.
The screen covers all available question/prompt fields in W/w19 kit/fixtures and the mirrored R0 VSTI item file. Full external evaluation corpora are not supplied in this kit.
TRACE_RULE_AMENDMENT.md specifies both Locate-line exceptions, numeric provenance, native gate changes, and the direct-packing limitation.
Form B follows the requested count-first numbered pattern; form A is unmeasured. No checkpoint evaluation, images, training, GPU, network, SSH, or external writes were used.
The orchestrator must decide trace-rule changes, native-division eligibility, and admission. The kit does not meet an all-native-checks-pass requirement.

Commands below produce all reported counts and checks from this workspace:
`PY=/scratch/jjyeung/envs/p1cpu/bin/python`; use `PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`.
`$PY -B prepare_inputs.py` produces the store census, source union, input hashes, source skips, and wording corpus.
`cc -O2 -shared -fPIC ned_filter.c -o ned_filter.so` builds the bounded edit-distance helper.
`$PY -B build_rows.py --census-only` fixes expected mechanical, eligible, and refusal counts.
`$PY -B build_rows.py` produces form B; `$PY -B build_rows.py --form A --out out/formA` produces form A and both histograms/native checks.
`$PY -B test_forms.py` produces the contract-test results.
`$PY -B audit_rows.py` and `$PY -B audit_rows.py --form A --out out/formA` independently recount identities, truth, cells, rooms, and removals.
`$PY -B finalize_kit.py` checks review receipts, cross-form IDs, native exclusions, and packages code, pinned inputs, rows, and reports.
`sha256sum out/sb_rowF.tar` reproduces the digest in out/sb_rowF.tar.sha256 and out/PACKAGE_RECEIPT.json.
The report contains no project-revision narrative; no borderline history sentences were retained.
