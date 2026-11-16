# Gravity contract call sites

The wrapper changes only the in-memory `GeometryContract.validate` attribute after restore. The runtime tree files remain byte-identical (`out/PIN_AUDIT.json`). Every unexecuted path below is a finding; the static census does not count as wrapper execution.

| Mode/path | Validator site | Capture binding | Execution evidence |
|---|---|---|---|
| Pilot: worker geometry kernel, geometry.prepare, prepare_one, convert, ground_profiles.load_geometry, scaled_from_heads | tree/student_pilot/geometry_profiles.py:119 | geometry.prepare opens `capture('dev-S1', native)` around GR.attempt | NOT EXECUTED; whole-worker pilot blocked. `test_guard.test_all_real_capture_decisions` also targets the load path, but is blocked. |
| Full: prepare_full_geometry, geometry kernel, convert, scaled_from_heads | tree/student_pilot/geometry_profiles.py:119 | Same explicit capture context | NOT EXECUTED; whole-worker full blocked. |
| Pilot: pair kernel, perception.load_geometry, ground_profiles.load_geometry, scaled_from_heads | tree/student_pilot/geometry_profiles.py:119 | perception.load_geometry resolves the clip in manifest records and opens its capture context | NOT EXECUTED; pilot blocked. |
| Full: nomdg.bind/validate_request(live=True), including repeated validation in worker.full and merge/admit paths, perception.load_geometry | tree/student_pilot/geometry_profiles.py:119 | Same explicit context for each newly loaded contract | NOT EXECUTED; full blocked. |
| Full: nomdg.run item loop, perception.load_geometry | tree/student_pilot/geometry_profiles.py:119 | Same explicit context | NOT EXECUTED; full blocked. |
| Pilot and full: perception.backend, ground_profiles.build_profile, GroundV3 | tree/student_pilot/ground_v3.py:90 | The same contract was bound by perception.load_geometry; Recorder retains its identity | NOT EXECUTED; both rehearsals blocked. |
| Legacy depth-head or metric G3T loading through ground_profiles.load_geometry, legacy_from_heads, ContractAdapter | tree/student_pilot/geometry_profiles.py:200 | Reader loads would inherit perception.load_geometry's context; direct tree callers need an explicit context | NOT EXECUTED. Current geometry.prepare emits scaled_g3t_depth, so this alternative profile does not arise in these worker paths. No proof is claimed for other readers. |

The reader contains no direct call to `GeometryContract.validate`; its geometry and perception loaders reach the constructors above. `read_runtime` validates the trainer configuration, a different method.

Installation tests in `out/tests/test_guard.py` cover source mismatch, terminal AST mismatch, a second install, foreign exception identity, earlier geometry errors, bound and unbound contracts, inverted conventions, unchanged passing geometry, and the real-capture census. They have not executed because the required interpreter is absent.
