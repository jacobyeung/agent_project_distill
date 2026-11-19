The four-file camera-form overlay is ready; the complete CPU suite has no new failure. Production composition and exact N exposure remain MISSING.

The base seal is `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7`; all 939 files match.
PATCH_A SHA256: `b95c1c618659a17b123b0d4d079fdf9ad53667f715e7362f43df0078bf6de477`.
PATCH_CAMFORM.patch is relative to base+PATCH_A. It applies with zero fuzz and reproduces all 943 edited-tree files. Donor/prior2 overlap: zero.

Enable `r1_training.camera_trace_form` with an absolute path/SHA256 pin to `configs/r1_camera_trace_form_v1.json` in the merged tree.
Policy SHA256: `169c439a1ac1bf11d66ee7b725277ef8ee07a706807324bed2696b9d99efaace`. Its bytes must remain available through ordinary pinned-input staging.
Absent field: unchanged composition bytes. A malformed pin or a policy with different contents refuses.
The policy applies CAM-ROT-WORDS-v1 and CAM-DIR-SYMBOL-v1 only to matching plan/canonical_text events in base camera_rotation and camera_movement_direction rows.
It regenerates response offsets, including a top-level span copy when present. Calls, response bytes/values, questions, options, answers, GT and other fields stay unchanged.
Slice rows retain their existing form. The receipt records the policy pin, implementation hash, source-code hashes, rule IDs and admitted rewrite counts per type/rule.
The copied rule function lives in fbp_cam/work/common.py and is called by build.py; both hashes are pinned.
Build SHA256: `39e8c067e319566ca31202b49c58470a147f4e556fc94ebeb86625c7d6b5544d`.
Common SHA256: `4535d0f1371268cd3590b477eea75f806c0156ff5b58b824261ee352b7d01712`.

All 6,000 authenticated P camera sources pass grammar a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268 and native c1_row/check_row, row_check, frame_metadata and replay checks after rewriting.
Rewrites: 2,000 rotation + 1,996 direction = 3,996. Unchanged: 2,000 displacement + 4 direction = 2,004.
All 6,000 printed-response answers recompute unchanged; all 6,000 targets equal the independently executed original fbp_cam rules.
All 5,979 delivered fbp_cam targets match by authenticated SOURCE_FORMS source-ID records: displacement 1,994, rotation 1,993, direction 1,992.
The other 21 counterpart rows are MISSING in `ro/orch_n30/fb_pack/cam/out/rows/camera_wording.jsonl`; SOURCE_TESTS.json gives each expected QID and exact path.
The requested 6,000-way delivered-output comparison is therefore incomplete; the 21 rows pass the same rule-code and native checks.

Composition over the authentic extract admits 6,000 rows through the real Rows.row reader and preserves every parallel SQLite target-column value.
The absent-field database, membership and receipt bytes equal base+PATCH_A at the same output path. Enabled receipt counts equal the 3,996 stored rewrites.
This harness mocks Filters to admit the extract; it proves composition behavior, not the unavailable production division/exclusions or full-base census.
Nine unit tests pass, covering policy pins, exact rules, offsets, unchanged types, idempotence, source inconsistency, admitted/refused counts and slice isolation.

Full CPU suite: base 1961 tests, 29 failures, 464 errors, 163 skips; overlay 1970 tests, 29 failures, 464 errors, 163 skips.
New failing test/error outcomes: 0. Existing failures, missing fixtures and sandbox restrictions remain; this is not a green full suite.
Nested headcall suite with its local fixture import path: base 69 tests, overlay 69 tests; each has 0 failures, 24 errors and 3 skips. New failing outcomes: 0.
SUITE_FAILURES.json retains every failing test and traceback; TESTS.json records the comparison. Both runs use the same guarded CPU harness and retain temporary files.

N's routing quota is 64 rows/step (r1_training.STREAMS). The full pinned N card, filtered camera counts and source shares are MISSING.
The available launch-test config references missing `tree_rebuild10_w/w24/work/build24f/launch_tests/u/c0167f682bd49fce84d1ca447a64131ae1605a345f534ce61ee98aabf7bee9c8` under the read-only mirror.
That config is not production N evidence. EXPOSURE.json records its exact path/pin and the missing production input fields.
Expected rewrites, conditional on extract match rates: B_rotation + 0.998*B_direction; if eligible camera type shares also match, 0.666*C, where C is the base camera count (MISSING).
For base draws r_rotation/r_direction per step: numeric rotation r_rotation becomes zero; word rotation zero becomes r_rotation.
Numeric direction 0.998*r_direction becomes zero; symbolic direction zero becomes 0.998*r_direction. The 0.002*r_direction rows without a negated option remain unchanged.
Already rewritten wording-slice draws are unaffected and must be added using their actual card/source shares (MISSING).
For reference only, r2_mix.table() gives nominal rotation 11.364486 and direction 15.192523 rows/step, before N card binding/caps/source mixing.
Under that conditional plan, numeric/symbolic direction exposure swaps 15.162138 draws/step and 0.030385 stays unchanged. These are not measured N draws.

Commands for all reported numbers, from the workspace; prefix each with `nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B`:
`code/setup.py`: base seal/files and PATCH_A authentication; `code/build_patch.py`: touched files, protected-path overlap and clean application.
`code/validate_sources.py`: extract authentication, matches/missing counterparts, rule counts, grammar/native checks and printed-answer recomputation.
`code/compose_extract.py`: exact absent-field bytes, stored-row preservation and enabled receipt counts; `code/exposure.py`: quota, conditional counts and draws.
With `TMPDIR=$PWD/work/unit_tmp PYTHONPATH=$PWD/work/new`, `-m unittest work/new/tests/test_r1_camera_trace_form.py -v`: nine unit tests.
`code/suite.py base` and `code/suite.py new`: complete CPU suites; `code/headcall_suite.py base` and `code/headcall_suite.py new`: nested suite; `code/finalize.py`: failure comparison, report, archive membership and SHA256.
Scripts that create immutable test outputs need fresh output directories for a rerun. Every delivered evidence JSON records its input hashes.

Delivery: PATCH_CAMFORM.patch, FILES_TOUCHED.json, TESTS.json, supporting evidence/code, fbp_camform.tar and fbp_camform.tar.sha256.
Verify the archive with `sha256sum -c out/fbp_camform.tar.sha256`. Bind the policy and final camera-source pin in the merged configuration, then reseal before production composition.
No-archaeology review: the before/after forms and base/overlay test counts are controlled comparisons; no historical wording is retained.
