PATCH_A2 fixes both MUST code changes. Full integration remains MISSING where the supplied kit lacks fixtures.

The sealed base has 939 files (`57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7`). The live copy has 940 files (`189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710`).
The live copy was authenticated with tree_rebuild15_w24l/out24j/TREE24J_SEAL.json; its three differences match the prompt.
PATCH_A2.patch replaces PATCH_A against the base (11 touched files). PATCH_A2_DELTA.patch changes 3 files against base+PATCH_A.
Both overlays reproduce the intended files exactly. The replacement applies to the live tree with --fuzz=0. No production seal was created.

Without routing_slice_declaration, compose_native uses source_names(specs) and the required routing_inputs lookup.
The deferred config still raises KeyError 'recovery'; missing routing_inputs still raises KeyError 'routing_inputs', before catalog loading or output creation.
An explicit deferred-composition guard follows source collection, preserving those legacy refusal points.
The unmocked SQLite regression starts with three replaced base cells: PATCH_A publishes rows.sqlite, membership.json and receipt.json; PATCH_A2 refuses and writes nothing.
CAMERA_SOURCE_SHA256 at student_pilot/r1_coverage.py:8 now binds e8cbda99f794540c9c0f716d1ae8ce451fd84e473598795c67237fe051acd2d0.
Declared and legacy six-family camera unit tests authenticate the final bytes, reject the 31914ba5 stand-in, and reject stand-in bytes paired with the final hash.
Those six-family unit tests isolate only the two absent coverage-file reads. Camera-only authentication runs without mocks; wording and other production gates remain required.

Counts below are tests/failures/errors/skips. Expected failures on base/PATCH_A demonstrate the fixes; subtest failures can exceed test counts.
Missing imports count as unittest loader errors; they do not establish that the affected test classes ran.
MUST regressions: base 11/7/0/0; PATCH_A 11/13/1/0; new 11/0/0/0; live 11/0/0/0.
The differential matrix checks 1,280 source_names cases, 192 validate_binding cases and 204 Membership/cell cases against base.
Subset declarations: base 11/43/39/0; new 11/0/0/0; live 11/0/0/0.
Focused: base 115/0/101/0; new 115/0/101/0; live 115/0/101/0.
Integration plus host: base 11/0/3/0; new 11/0/3/0; live 11/0/3/0.
Live host coverage: 15 distinct tests pass on the unpatched live tree and 15 on the patched live tree; no host case remains skipped.
Mode-p byte comparison with the sealed-base sibling reference: unpatched 1/0/0/0; patched 1/0/0/0.
Real-envelope declaration checks: base 7/6/0/0; new 7/5/0/0; live 7/5/0/0.
Full discovery: base 1930/18/473/145; new 1944/18/473/145; live 1959/18/473/145.
Focused, integration, host and full comparisons have identical pre-existing failure text and multiplicity after temporary-path normalization; no new failure was observed.
BASE_FAILURES.json records each failing test, cause and traceback. TESTS.json records commands, input hashes, comparisons and every attempted module.
The original 32-module gate manifest and original review corpus were not supplied (MISSING). Full tree discovery and the explicit 256-subset × five-config matrix were run; no review list was guessed.
MISSING_INPUTS.json gives exact missing paths and affected tests, including the w21 fixture root. The current copy does contain the authentic naming_remove.json.
Unisolated six-family validation is MISSING: ro/n30_mirror/dist_diag/coverage_v2h/COVERAGE_DISTANCE_V2H.jsonl and COVERAGE_UNITS_V2H.jsonl are absent.

Project LOCALIZED_ROW_SOURCES.json exactly as: {k: v for k, v in raw.items() if k in set(bound) | {"room", "room_programs_excluded"}}.
This preserves the original family pins and removes command/inputs metadata. Re-pin the projected document; declared_names still refuses a missing bound family.
Known difference retained: declared six-family composition places recovery fifth; legacy composition places recovery first.
Overlap: camform shares student_pilot/r1_routing.py; prior2 shares student_pilot/r1_population.py; donor and pointD share no file.
OVERLAP.json records all four authenticated manifests and the camform application check.
Camform's PATCH_CAMFORM.patch applies on top with --fuzz=0; its combined regression suite is 23/0/0/0.

Commands for all numbers (run from this workspace; prefix each Python invocation below with the exact prefix on the next line):
`env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B`
`work/verify_base.py` verifies the base inventory; `work/setup.py` verifies PATCH_A, the live inventory and camera hashes.
`work/build_patch.py` builds both overlays, verifies each application, inventories overlaps and applies camform.
`work/refresh_overlap.py` authenticates the final neighboring manifests and verifies that the tested camform patch is unchanged.
`work/run_matrix.py` serially runs subset, focused, integration, live-host, camform and full suites; RUN_MATRIX.json gives each expanded command.
`work/run_supplement.py` runs final MUST comparisons and real-envelope declarations; SUPPLEMENT.json gives each expanded command.
`work/enable_host_reference.py` supplies the sealed-base sibling path.
`work/run_tests.py live_base host_ref_live_base tests.test_host24j.HostReceipt.test_mode_p_bytes_match_base` and `work/run_tests.py live host_ref_live tests.test_host24j.HostReceipt.test_mode_p_bytes_match_base` run the byte comparisons.
`work/summarize.py` computes failure comparisons and counts; `work/package.py` checks source hashes and produces this report, tar and SHA256 sidecar.
The harness is CPU-only, retains fixtures, denies network/subprocess workers/NFS reads/deletion/outside writes, and caps final-run thread pools at 16.
Delivery: PATCH_A2.patch, PATCH_A2_DELTA.patch, FILES_TOUCHED.json, TESTS.json, fbp_patchA2.tar and fbp_patchA2.tar.sha256. The tree owner must merge and reseal.
