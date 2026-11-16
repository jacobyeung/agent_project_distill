# EAT-1 report: eat1.adapters.b04_tiny:make_reader

Artifact manifest /scratch/jjyeung/orch_n30/b03_e2etest/work/b04_tiny/artifact/ARTIFACT.json (sha256 992732f9c102959735649816961628573f19fa065f687653d95d93901623d93a); items 4; mode dynamic; started 2026-11-16T14:48:41Z.

| Clause | Status | Summary |
|---|---|---|
| A1 | PASS | 2 artifact, 3 code, 0 input, 0 outside-artifact data files opened after generate() started |
| A2 | PASS | model entries per item {1: 4}; 0 tokens fed that neither the model chose nor a registered handler emitted; 0 static findings |
| A3 | FAIL | 7 findings in 8 call-path files {'A3.constant': 5, 'A3.table_load': 1, 'A3.threshold': 1} |
| A4 | FAIL | 6 offender groups (3 static) |
| A5 | INCOMPLETE | parts {'iii': 'PASS', 'i': 'NOT RUN', 'ii': 'NOT RUN'} |

Overall: **FAIL**

## Per type (A6)

| Type | Items | Call rate | Calls/item | Heads behind response fields | s/item (mean, median, max) |
|---|---|---|---|---|---|
| camera | 1 | 0.000 | 0.00 | - | 0.130, 0.130, 0.130 |
| direct | 1 | 0.000 | 0.00 | - | 0.046, 0.046, 0.046 |
| ground | 1 | 0.000 | 0.00 | - | 0.112, 0.112, 0.112 |
| room | 1 | 0.000 | 0.00 | - | 0.109, 0.109, 0.109 |

## Fixture files excluded from the call path

- /scratch/jjyeung/orch_n30/b04_e2ehook/tests/test_tiny_e2e.py

## Offenders by clause (file and line)

### A3

- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/geometry_profiles.py:125 (ProfileGeometry.__init__): constant 1000 — `self.grid_uv = np.asarray(np.linspace(0, 1000, self.depth_grid.shape[1]) if grid_uv is None else grid_uv)`
- `A3.table_load` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/artifact.py:282 (load_tensors): load() — `return load(f.read())`
- `A3.threshold` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/callhook.py:91 (CallHook.push_sampled): compares against MAX_CALL_TOKENS — `if self.active is not None and (tail.endswith('>') or len(ids) - self.active > MAX_CALL_TOKENS):`
- `A3.constant` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/geometry.py:64 (from_tower): constant 32 — `C = np.repeat(np.eye(4)[None], 32, axis=0)`
- `A3.constant` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/geometry.py:67 (from_tower): constant 32 — `K = np.zeros((32, 3, 3))`
- `A3.constant` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/geometry.py:71 (from_tower): constant 1000 — `A = np.repeat(np.diag([W / 1000, H / 1000, 1.])[None], 32, axis=0)`
- `A3.constant` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/geometry.py:71 (from_tower): constant 32 — `A = np.repeat(np.diag([W / 1000, H / 1000, 1.])[None], 32, axis=0)`

### A4

- reader_error x2 items ['camera_0', 'ground_0']  {"detail": "PermissionError: e2e_artifact_refuses:code_outside_manifest:/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/__init__.py"}
- answer_not_in_generated_sequence x2 items ['camera_0', 'ground_0']  {"answer": null}
- reported_text_differs_from_generated_sequence x4 items ['camera_0', 'direct_0', 'ground_0', 'room_0']  {}
- `A4.guard` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/geometry_profiles.py:55 (GeometryContract): identifier ground_truth_substitution — `ground_truth_substitution: bool = False`
- `A4.guard` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/artifact.py:198 (_patch_native): identifier _guarded — `wrapper = _NATIVE.setdefault(id(original), (original, _guarded(original)))[1]`
- `A4.except_substitute` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/callhook.py:126 (CallHook.respond): except-handler returns a substitute — `return []`

