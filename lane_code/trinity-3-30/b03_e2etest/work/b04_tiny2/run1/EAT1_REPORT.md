# EAT-1 report: eat1.adapters.b04_tiny:make_reader

Artifact manifest /scratch/jjyeung/orch_n30/b03_e2etest/work/b04_tiny2/artifact/ARTIFACT.json (sha256 cbb217f45d4d285bf183508d6940f726edad593372dd886b4cff438a0493e351); items 4; mode dynamic; started 2026-11-16T14:49:02Z.

| Clause | Status | Summary |
|---|---|---|
| A1 | PASS | 2 artifact, 32 code, 0 input, 0 outside-artifact data files opened after generate() started |
| A2 | FAIL | model entries per item {1: 4}; 0 tokens fed that neither the model chose nor a registered handler emitted; 3 static findings |
| A3 | FAIL | 142 findings in 41 call-path files {'A3.table_load': 1, 'A3.threshold': 5, 'A3.constant': 121, 'A3.unit_conversion': 13, 'A3.data_file': 2} |
| A4 | FAIL | 15 offender groups (14 static) |
| A5 | FAIL | parts {'iii': 'PASS', 'i': 'PASS', 'ii': 'FAIL'} |

Overall: **FAIL**

## Per type (A6)

| Type | Items | Call rate | Calls/item | Heads behind response fields | s/item (mean, median, max) |
|---|---|---|---|---|---|
| camera | 1 | 1.000 | 3.00 | move: {'g3t,scale_head': 1}; turn: {'g3t': 1}; pose: {'g3t,scale_head': 1} | 0.507, 0.507, 0.507 |
| direct | 1 | 0.000 | 0.00 | - | 0.046, 0.046, 0.046 |
| ground | 1 | 1.000 | 3.00 | ground: {'sam3,selector_head,g3t,scale_head': 2}; gap: {'sam3,selector_head,g3t,scale_head': 1} | 0.937, 0.937, 0.937 |
| room | 1 | 0.000 | 0.00 | - | 0.110, 0.110, 0.110 |

## Fixture files excluded from the call path

- /scratch/jjyeung/orch_n30/b04_e2ehook/tests/test_tiny_e2e.py

## Offenders by clause (file and line)

### A2

- `A2.response_outside_model` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/head_programs.py:191 (<module>): response text built outside a torch module method — `RESPONSE_SPAN = re.compile(r'<tool_response>(.*?)</tool_response>', re.S)`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/p3_grammar.py:7 (<module>): response text built outside a torch module method — `RESPONSE_TOKENS = ('<tool_response>', '</tool_response>')`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/ground_v312.py:40 (wrap): response text built outside a torch module method — `return '<tool_response>\n' + body + '\n</tool_response>'`

### A3

- `A3.table_load` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/artifact.py:282 (load_tensors): load() — `return load(f.read())`
- `A3.threshold` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/callhook.py:91 (CallHook.push_sampled): compares against MAX_CALL_TOKENS — `if self.active is not None and (tail.endswith('>') or len(ids) - self.active > MAX_CALL_TOKENS):`
- `A3.constant` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/geometry.py:64 (from_tower): constant 32 — `C = np.repeat(np.eye(4)[None], 32, axis=0)`
- `A3.constant` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/geometry.py:67 (from_tower): constant 32 — `K = np.zeros((32, 3, 3))`
- `A3.constant` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/geometry.py:71 (from_tower): constant 1000 — `A = np.repeat(np.diag([W / 1000, H / 1000, 1.])[None], 32, axis=0)`
- `A3.constant` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/geometry.py:71 (from_tower): constant 32 — `A = np.repeat(np.diag([W / 1000, H / 1000, 1.])[None], 32, axis=0)`
- `A3.constant` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/geometry.py:95 (camera_geometry): constant 32 — `pose = np.empty((32, 9), dtype=np.float64)`
- `A3.constant` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/geometry.py:95 (camera_geometry): constant 9 — `pose = np.empty((32, 9), dtype=np.float64)`
- `A3.constant` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/geometry.py:96 (camera_geometry): constant 33 — `for k in range(1, 33):`
- `A3.constant` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/grounding.py:84 (mask_pixels): constant 1000 — `return np.column_stack(((cols + .5) / w * 1000, (rows + .5) / h * 1000))`
- `A3.constant` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/grounding.py:133 (StageOneSocket.__call__): constant 32 — `masks = np.zeros((32,) + self.mask_shape, bool)`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_config.py:5 (<module>): constant 0.1 — `'pose_weight': 0.0, 'depth_weight': 0.0, 'warmup_ratio': 0.1,`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_config.py:6 (<module>): constant 128 — `'head_width': 128, 'depth_grid': 4, 'translation_unit_m': 1.0,`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_config.py:7 (<module>): constant 32 — `'temporal_patch_size': 2, 'frame_count': 32,`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_config.py:16 (<module>): constant 0.3 — `'reason_mix_prob': 0.3, 'reason_mix_start': 0.3,`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_losses.py:295 (video_features): constant 16 — `def video_features(hidden, batch, video_token_id, merge_size, tokens=False, any_groups=False, max_groups=16):`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_reason.py:32 (<module>): constant 0.05 — `CLIP = {'DIST': (0.05, 30.0), 'DEPTH': (0.05, 30.0), 'SIZE': (1.0, 1000.0)}`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_reason.py:32 (<module>): constant 30.0 — `CLIP = {'DIST': (0.05, 30.0), 'DEPTH': (0.05, 30.0), 'SIZE': (1.0, 1000.0)}`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_reason.py:32 (<module>): constant 1000.0 — `CLIP = {'DIST': (0.05, 30.0), 'DEPTH': (0.05, 30.0), 'SIZE': (1.0, 1000.0)}`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_reason.py:33 (<module>): constant 999 — `COUNT_MAX = 999`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_reason.py:34 (<module>): constant 200.0 — `COORD_LIMIT = 200.0`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_reason.py:36 (<module>): constant 50.0 — `OUTPUT_LIMIT = 50.0`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_reason.py:37 (<module>): constant 16 — `GROUPS = 16`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_reason.py:38 (<module>): constant -100 — `IGNORE = -100`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_reason.py:177 (angle_target): identifier degrees — `def angle_target(degrees):`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/auxiliary_reason.py:193 (<module>): def angle_degrees — `def angle_degrees(sine, cosine):`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/camera_head.py:18 (<module>): constant 9 — `TARGET_DIM = 9`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/camera_head.py:21 (canon_unit_quat): constant 1e-06 — `def canon_unit_quat(q, fallback=None, eps=1e-6):`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/camera_head.py:69 (Block.__init__): constant 0.01 — `def __init__(self, dim, heads, mlp_ratio=4, init_values=0.01):`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/camera_head.py:87 (CameraHead.__init__): constant 16 — `def __init__(self, dim, depth=4, heads=16, has_gravity=False, has_scale=False, has_g3t_prior=False,`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/camera_targets.py:33 (quaternion_xyzw): constant 0.25 — `q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s]`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/camera_targets.py:39 (quaternion_xyzw): constant 0.25 — `q = [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_data.py:20 (pointing_token_weights): constant 5.0 — `def pointing_token_weights(labels, decode, decision=5.0, row_mean=2.0):`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_data.py:83 (nested_indices): constant 64 — `def nested_indices(anchors, count=64):`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_data.py:449 (mixed_indices): constant 17 — `def mixed_indices(counts, steps, seed=17, start_step=0, training_mode='mixed', mix=None, world=8):`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_data.py:449 (mixed_indices): constant 8 — `def mixed_indices(counts, steps, seed=17, start_step=0, training_mode='mixed', mix=None, world=8):`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_decode.py:39 (<module>): constant 96 — `MAX_CALL_TOKENS = 96`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_decode.py:251 (_prepare_decode): constant 200 — `def _prepare_decode(model, processor, batch, *, max_new_tokens=None, mode='own', donor_batch=None, max_calls=200,`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_decode.py:432 (generate): constant 200 — `def generate(model, processor, batch, *, max_new_tokens=None, mode='own', donor_batch=None, max_calls=200,`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_decode.py:456 (_generate_one): constant 200 — `def _generate_one(model, processor, batch, *, max_new_tokens=None, mode='own', donor_batch=None, max_calls=200,`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_routing.py:119 (wrap): constant 180 — `return (deg + 180) % 360 - 180 if (deg + 180) % 360 else 180`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_routing.py:119 (wrap): constant 360 — `return (deg + 180) % 360 - 180 if (deg + 180) % 360 else 180`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_routing.py:264 (OwnGeometry.pose): identifier yaw_degree — `yaw_degree=round(math.degrees(math.atan2(-level[0][2], level[2][2]))))`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_routing.py:264 (OwnGeometry.pose): identifier degrees — `yaw_degree=round(math.degrees(math.atan2(-level[0][2], level[2][2]))))`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_routing.py:300 (OwnGeometry.turn_text): identifier degrees — `turn = wrap(round(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], float(a @ b)))))`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_v.py:16 (<module>): constant 33 — `ANCHORS = list(range(2, 33, 2))`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_v.py:17 (<module>): constant 1600 — `RECIPE = dict(steps=1600, global_batch=64, world_size=8, warmup_ratio=.03,`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_v.py:17 (<module>): constant 64 — `RECIPE = dict(steps=1600, global_batch=64, world_size=8, warmup_ratio=.03,`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_v.py:17 (<module>): constant 8 — `RECIPE = dict(steps=1600, global_batch=64, world_size=8, warmup_ratio=.03,`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_v.py:17 (<module>): constant 0.03 — `RECIPE = dict(steps=1600, global_batch=64, world_size=8, warmup_ratio=.03,`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_v.py:18 (<module>): constant 0.0001 — `learning_rate=1e-4, weight_decay=.01, milestones=[200, 400, 800, 1600], seed=17)`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_v.py:18 (<module>): constant 0.01 — `learning_rate=1e-4, weight_decay=.01, milestones=[200, 400, 800, 1600], seed=17)`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_v.py:18 (<module>): constant 200 — `learning_rate=1e-4, weight_decay=.01, milestones=[200, 400, 800, 1600], seed=17)`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_v.py:18 (<module>): constant 400 — `learning_rate=1e-4, weight_decay=.01, milestones=[200, 400, 800, 1600], seed=17)`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_v.py:18 (<module>): constant 800 — `learning_rate=1e-4, weight_decay=.01, milestones=[200, 400, 800, 1600], seed=17)`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_v.py:18 (<module>): constant 1600 — `learning_rate=1e-4, weight_decay=.01, milestones=[200, 400, 800, 1600], seed=17)`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_v.py:18 (<module>): constant 17 — `learning_rate=1e-4, weight_decay=.01, milestones=[200, 400, 800, 1600], seed=17)`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_vc.py:12 (<module>): constant 1e-05 — `VC_RECIPE = {**RECIPE, 'encoder_learning_rate': 1e-5}`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_vc.py:15 (<module>): constant 1200 — `VC_BATCH4H_RECIPE = {**VC_RECIPE, 'steps': 1200, 'milestones': [200, 400, 800, 1200]}`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/decoupled_vc.py:15 (<module>): constant 200 — `VC_BATCH4H_RECIPE = {**VC_RECIPE, 'steps': 1200, 'milestones': [200, 400, 800, 1200]}`
- ... 82 more in EAT1_REPORT.json

### A4

- response_cites_undeclared_module x6 items ['camera_0', 'ground_0']  {"modules": ["g3t"], "call": "<move from=1 to=9>"}
- `A4.guard` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/artifact.py:198 (_patch_native): identifier _guarded — `wrapper = _NATIVE.setdefault(id(original), (original, _guarded(original)))[1]`
- `A4.except_substitute` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/callhook.py:126 (CallHook.respond): except-handler returns a substitute — `return []`
- `A4.guard` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/camera_head.py:21 (canon_unit_quat): identifier fallback — `def canon_unit_quat(q, fallback=None, eps=1e-6):`
- `A4.guard` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:55 (GeometryContract): identifier ground_truth_substitution — `ground_truth_substitution: bool = False`
- `A4.guard` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/ground_context.py:13 (GroundContext): identifier fallback — `fallback: object`
- `A4.guard` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/tower_errors.py:9 (<module>): def tower_guard — `def tower_guard(function):`
- `A4.status_literal` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:182 (BoxRegistry.invalidate): string 'not seen' — `def invalidate(self, name, state='not seen'):`
- `A4.status_literal` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:226 (BoxRegistry.gap): string 'not seen' — `states=[self.states.get(n,'not seen') for n in names]`
- `A4.status_literal` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:227 (BoxRegistry.gap): string 'not seen' — `for status in ('unresolved','not seen','box unavailable'):`
- `A4.status_literal` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:227 (BoxRegistry.gap): string 'box unavailable' — `for status in ('unresolved','not seen','box unavailable'):`
- `A4.status_literal` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:518 (ground): string 'not seen' — `else 'not seen' if not entries else None)`
- `A4.guard` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/ground_v312.py:18 (<module>): class RowRefusal — `class RowRefusal(ValueError):`
- `A4.guard` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/program_errors.py:2 (<module>): class ProgramRefusal — `class ProgramRefusal(ValueError):`
- `A4.guard` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/room_v314.py:22 (<module>): class RoomRefusal — `class RoomRefusal(ValueError):`

### A5

- response_names_module_but_did_not_change x3 items ['ground_0']  {"module": "selector_head", "call_index": 0}

