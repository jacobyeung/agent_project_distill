GO AFTER FIXES (MUST items)

Patch `PATCH_A.patch` (sha256 b95c1c61…de477, verified) applies cleanly with `patch -p1` to a copy of the live base and reproduces all ten new hashes in FILES_TOUCHED.json.
One code fix is required: a deferred-first-boundary config no longer refuses in `compose_native`. The merge must also replace the stand-in camera pin.

## Base seal
The live tree no longer matches seal 57a1f14d…: its 940 files digest to 189df6ac…, which matches the current TREE_SEAL.json and TREE_FILES.sha256.
Against the builder's 939-file inventory, `launch_r1/entry.py` and `launch_r1/production_proof.py` changed and `tests/test_host24j.py` is new. The patch touches none of these three.
I therefore compared only the patch-touched files: all nine touched base files match the builder's base hashes. The owner must reseal against the current base.

## MUST
1. `student_pilot/r1_routing.py:177` now calls `source_names(specs, cfg)`, and `:186` reads `cfg['r1_training'].get('routing_inputs', {})`. Both change legacy behavior.
   For a `routing_slices: deferred_first_boundary` config, base refuses (KeyError 'recovery'). The patched tree instead composes and writes `rows.sqlite`, `membership.json` and `receipt.json`, after dropping the base recovery, distance and unit rows.
   For a full legacy config without `routing_inputs`, base refuses at once (KeyError 'routing_inputs'). The patched tree refuses only after the catalog check and the base pass (KeyError of the first family).
   Neither case reaches admission: `s1_admission.py:212` calls `compose_native` only when the config is not deferred, and the deferred gate refuses a routing base that carries a source membership.
   It still contradicts the claim that legacy configs are unchanged. Fix: use `cfg` and `.get` only when `routing_declaration(cfg)` is not None, or refuse `deferred(cfg)` explicitly in `compose_native`.
2. Before merge: `student_pilot/r1_coverage.py:8` binds the stand-in 31914ba5… (the route lane's `out/rows/camera_wording.jsonl`). The pin is the only camera constant, and the old pin e3c72962… appears nowhere else.
   As shipped, the tree authenticates that file: six-family and legacy six-family configs pass `validate_binding` and reach the host veto. Replace the pin with the final camera sha, then reseal.

## Verified claims
- Declaration: the schema has exactly the keys {schema, bound, deferred}. `bound` must be a list of unique strings and `deferred` a dict, and every deferred family needs a non-blank string reason. Any other shape refuses with a named error.
- An exact path/sha pin is required; a changed, missing or extra-field pin refuses. A declaration plus `routing_slices` refuses with R1_ROUTING_DECLARATION_WITH_DEFERRED.
- Subsets: all 64 subsets return canonical ROUTING_FAMILIES order under 4 random bound and source orderings each, with or without the room audit names.
- Named refusals: 192 missing-source, 192 undeclared-source, 192 overlap, 192 gap and 960 bad-reason cases each refuse with the exact family named.
- Legacy: 1,280 legacy `source_names` cases (2^8 key sets × 5 configs) match base exactly. Legacy `validate_binding` and `Membership` without a config match base except the intended camera pin.
- Identity: the declaration pin is part of config identity. `carrier_c1_run.py:38-43` and `r1_training.py:105-107` exclude only fixed keys, and the identity changes whenever the declaration changes.
- Records: the composed receipt and the membership record the declaration pin and the deferred reasons.
- Membership: it refuses a configured/embedded declaration mismatch, a changed deferred map, undeclared sources and missing sources. It accepts a relocated declaration with the same sha.
- Real route (trinity-1-18, unset environment; real config, envelopes, catalogs, removals and exclusions; only the routing base is a stand-in, since its database and division exist only on the frame host):
  the four-family (recovery and camera deferred), five- and six-family declarations, the legacy six-family config, each single family, and four families with Q_E7=1 all refuse at the Trinity veto (`r2_intake.py:43`: "Local slices must contain at most 2000 rows per family").
- Real-route refusals by name: UNDECLARED:recovery:envelope, ENVELOPE_MISSING:recovery, ENVELOPE_MISSING_OR_CHANGED:recovery, UNDECLARED:camera_wording:{source,catalog,staged_source}, COVERAGE_SOURCE_PIN:coverage_units, SLICE_MANIFEST_DIFFERS:absolute_distance, WORDING_EXCLUSION_REQUIRED, CAMERA_WORDING_REQUIRED, NAMING_REMOVAL_ORDER and DEFERRED_REASON_REQUIRED.
- Downstream: `launch_r1/entry.py:96` (`routing_requirements.require`) still requires recovery and unit rows, so a recovery-deferred config refuses later with RECOVERY_ROWS_ABSENT. Nothing is waived.
- Alias: the six files are byte-identical to FHALIAS2_REPORT's before and after hashes (`ALIAS2.patch` is absent at the named /data2 path). The local-node and Trinity vetoes are kept at `r2_intake.py:40-41` and `r2_materialize.py:22-24`, and `Q_E7` is cleared at `host.py:253` and `distributed.py:77`.
- Scope: no unrelated change. The 10 touched files hold only the declaration, the camera constant, the alias and the new test.

## Notes (not blocking)
- With a declaration, `row_sources` must hold only the bound families plus the room audit names. The route lane's LOCALIZED_ROW_SOURCES.json also carries `command` and `inputs` and must be projected, as the builder's report says.
- Order differs: a six-family declaration composes recovery fifth, while legacy composes it first (SLICE_CELLS), so the row offsets differ for the same six sources.
- `Membership(cfg=None)` trusts the membership's embedded pinned declaration. Every production caller passes `cfg` (`r1_routing.py:151`, `r1_population.py:119`).

## Tests (CPU, trinity-1-18; NFS reads, writes outside this folder, sockets, subprocesses and deletion blocked)
| Suite | Base | New |
|---|---|---|
| `test_r1_subset` (11) | 43 failures (76 subtests), 39 errors | all pass |
| Focused (111 of the builder's 115) | 0 failures, 36 errors | 0 failures, 36 errors, same tests |
| Integration plus host (4) | all pass | all pass |
| Gate: 32 modules importing changed code (288) | 6 failures (5 subtests), 12 errors, 1 skip | identical outcomes |
| Real route (25 cases) | declaration ignored, legacy refusals | all as expected |

- Missing harness pieces: four focused support modules and `alias2_tests` were not delivered with the builder's work folder, so I did not run them.
- Errors fixed by the real paths: naming_remove.json (sha d1454a44…) and w21 INIT_INPUT.json now resolve, so the builder's 101 INIT_INPUT errors are gone.
- The remaining errors predate the patch and appear identically on base and new: lane-relative inputs absent from the w21 fixture root (`tree_b01ce449`, `build15`, `build_n1`, `n1fix2`), the node-local archive-reserve check (`test_r2_build5_persistence`, `test_r2_build4`), and an ImportError in a module generated by `test_r2_build8`.

## Reproduce (from work/, with `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B`)
- Seal: `verify_seal.py`. Tests: `run_tests.py <base|new> <label> <target>`, where the target is `tests.test_r1_subset` (run base as `base_t`), `@focused_names.json`, `@integration_names.json`, `@gate_names.json`, `rev_real_route` or `rev_subset`.
- Outcomes: `work/results/*.json`.
- Scratch size: `work/` is 762 MB, over the 500 MB cap. The gate runs kept about 610 MB of test fixtures in `work/test_runs/gate_*`, and I left them because deletion is not allowed here.
