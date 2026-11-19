PATCH_CAMFORM2 fixes M1, S1 and S2. The full CPU comparison has no new failing outcome.

M1: A present camera_trace_form field in deferred mode raises R1_CAMERA_TRACE_FORM_REQUIRES_COMPOSITION during config validation, before other validation or policy reads.
The shared deferred gate also refuses this combination in admission and launch paths.
S1: The policy pin must equal 169c439a1ac1bf11d66ee7b725277ef8ee07a706807324bed2696b9d99efaace; reformatted and reordered copies refuse.
S2: Receipts retain rewritten-row counts and add changed_base_lines, changed_base_lines_by_type and changed_base_lines_by_rule.
Two matching events in one admitted row count as one rewritten row and two changed lines; repeated matches on one physical line count once.

PATCH_CAMFORM2.patch targets seal 57a1f14d + PATCH_A b95c1c61, includes the complete camera overlay, touches 7 files, and applies with zero fuzz.
The sealed base verifies 939 files; clean application reproduces 944 final files.
PATCH_CAMFORM2.patch SHA256: 7e7ae484d15ea0209eaca09faef483794e309c8f1141a8b059be1cb971a91dff.
PATCH_CAMFORM2_ON_A2.patch applies with zero fuzz; declaration-mode absent bytes match base+PATCH_A2; 29 focused A2 tests pass.

Focused tests: 26 pass, including all nine existing camera tests, six review regressions and 11 routing-subset tests.
The six review tests produce eight failure outcomes and two missing-counter errors on PATCH_CAMFORM; all six pass on PATCH_CAMFORM2.
All 6,000 authenticated source rows pass native checks, grammar, preservation checks and unchanged printed-answer recomputation.
Declaration mode binds the exact e8cbda99f794540c9c0f716d1ae8ce451fd84e473598795c67237fe051acd2d0 camera_wording source.
Composition admits 11,979 rows: 6,000 base rows plus all 5,979 delivered slice rows; deferred(cfg) is false.
With the field absent, rows.sqlite, membership.json and receipt.json are byte-identical to base+PATCH_A at the same output path.
Enabled counts are 2,000 rotation rows/lines and 1,996 direction rows/lines; all 5,979 slice rows and all 11,979 parallel target-column values remain unchanged.
All 5,979 base/slice counterpart targets match when enabled; 1,998 match when absent. Filters see the unrewritten base rows.
Filters are mocked to admit the extract; source binding, Rows.row checks and composition run natively. This proves composition behavior, not production admission.
MISSING: 21 delivered counterpart QIDs, listed in SOURCE_TESTS.json, expected at /scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/fb_pack/cam/out/rows/camera_wording.jsonl.

Full CPU suite on PATCH_A: base 1961 tests, 29 failures, 464 errors, 163 skips; overlay 1976 tests, 29 failures, 464 errors, 163 skips.
Nested headcall: base/new 69/69 tests, 0/0 failures, 24/24 errors, 3/3 skips.
Both comparisons introduce zero failing outcomes. Existing fixture/sandbox failures remain; the full suite is not green. TESTS.json and SUITE_FAILURES.json retain results and tracebacks.

Run commands from this workspace with prefix: `nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B`.
`code/setup.py` produces seal/file checks; `code/package_patch.py` produces patch/file/application counts; `code/package_A2.py` checks the conditional A2 delivery.
`code/regressions.py before` and `code/regressions.py after` produce the fail-before/pass-after counts; `code/unit.py` produces focused counts.
`code/validate_sources.py` produces source, native-check and counterpart counts; `code/compose_declaration.py A` produces all declaration-mode composition numbers.
`code/suite.py base` and `code/suite.py new` produce full-suite counts; `code/headcall_suite.py base` and `code/headcall_suite.py new` produce nested-suite counts.
`code/finalize.py` compares failing test IDs/outcome multiplicities and builds the archive. Every delivered evidence JSON records input SHA256 hashes.
PATCH_A2 is authenticated by fbp_patchA2.tar.sha256 and byte equality with out/PATCH_A2.patch inside that archive.
`code/compose_A2.py` and `code/unit_A2.py` produce A2 composition and focused-test counts.
Verify the bundle with `sha256sum -c out/fbp_camform2.tar.sha256`. Controlled base/overlay comparisons are retained as evidence; no revision-history prose is retained.
