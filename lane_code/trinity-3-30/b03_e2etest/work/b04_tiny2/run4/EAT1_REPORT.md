# EAT-1 report: eat1.adapters.b04_tiny:make_reader

Artifact manifest /scratch/jjyeung/orch_n30/b03_e2etest/work/b04_tiny2/artifact/ARTIFACT.json (sha256 cbb217f45d4d285bf183508d6940f726edad593372dd886b4cff438a0493e351); items 4; mode dynamic; started 2026-11-16T14:56:07Z.

| Clause | Status | Summary |
|---|---|---|
| A1 | PASS | 2 artifact, 32 code, 0 input, 0 outside-artifact data files opened after generate() started |
| A2 | PASS | model entries per item {1: 4}; 0 tokens fed that neither the model chose nor a registered handler emitted; 0 static findings |
| A3 | FAIL | 39 findings in 20 call-path files {'A3.threshold': 5, 'A3.constant': 30, 'A3.unit_conversion': 4} |
| A4 | FAIL | 6 offender groups (5 static) |
| A5 | PASS | parts {'iii': 'PASS', 'i': 'PASS', 'ii': 'PASS'} |

Overall: **FAIL**

## Per type (A6)

| Type | Items | Call rate | Calls/item | Heads behind response fields | s/item (mean, median, max) |
|---|---|---|---|---|---|
| camera | 1 | 1.000 | 3.00 | move: {'g3t,scale_head': 1}; turn: {'g3t': 1}; pose: {'g3t,scale_head': 1} | 0.482, 0.482, 0.482 |
| direct | 1 | 0.000 | 0.00 | - | 0.042, 0.042, 0.042 |
| ground | 1 | 1.000 | 3.00 | ground: {'sam3,selector_head,g3t,scale_head': 2}; gap: {'sam3,selector_head,g3t,scale_head': 1} | 1.015, 1.015, 1.015 |
| room | 1 | 0.000 | 0.00 | - | 0.104, 0.104, 0.104 |

## Fixture files excluded from the call path

- /scratch/jjyeung/orch_n30/b04_e2ehook/tests/test_tiny_e2e.py

## Offenders by clause (file and line)

### A3

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
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/camera_targets.py:33 (quaternion_xyzw): constant 0.25 — `q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s]`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/camera_targets.py:39 (quaternion_xyzw): constant 0.25 — `q = [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_routing.py:119 (wrap): constant 180 — `return (deg + 180) % 360 - 180 if (deg + 180) % 360 else 180`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_routing.py:119 (wrap): constant 360 — `return (deg + 180) % 360 - 180 if (deg + 180) % 360 else 180`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_routing.py:264 (OwnGeometry.pose): identifier yaw_degree — `yaw_degree=round(math.degrees(math.atan2(-level[0][2], level[2][2]))))`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_routing.py:264 (OwnGeometry.pose): identifier degrees — `yaw_degree=round(math.degrees(math.atan2(-level[0][2], level[2][2]))))`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/carrier_c1_routing.py:300 (OwnGeometry.turn_text): identifier degrees — `turn = wrap(round(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], float(a @ b)))))`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:125 (ProfileGeometry.__init__): constant 1000 — `self.grid_uv = np.asarray(np.linspace(0, 1000, self.depth_grid.shape[1]) if grid_uv is None else grid_uv)`
- `A3.threshold` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:143 (ProfileGeometry.has): compares against 32 — `return type(frame) is int and 1 <= frame <= 32`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:143 (ProfileGeometry.has): constant 32 — `return type(frame) is int and 1 <= frame <= 32`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:156 (ProfileGeometry._raw_depth): constant 1000 — `x, y = np.clip(np.asarray(uv) * ((len(d)-1)/1000), 0, len(d)-1).T`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:178 (ProfileGeometry.lift): constant -10 — `offsets = np.array([(dx,dy) for dx in np.linspace(-10,10,5) for dy in np.linspace(-10,10,5)])`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:178 (ProfileGeometry.lift): constant 10 — `offsets = np.array([(dx,dy) for dx in np.linspace(-10,10,5) for dy in np.linspace(-10,10,5)])`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:178 (ProfileGeometry.lift): constant 5 — `offsets = np.array([(dx,dy) for dx in np.linspace(-10,10,5) for dy in np.linspace(-10,10,5)])`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:179 (ProfileGeometry.lift): constant 1000 — `stencil = np.clip(uv[:,None]+offsets,0,1000)`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:180 (ProfileGeometry.lift): constant 25 — `d = self.depth(frame, stencil.reshape(-1,2)).reshape(len(uv),25)`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:181 (ProfileGeometry.lift): constant 20 — `p20,p50,p80 = np.percentile(d,(20,50,80),axis=1)`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:181 (ProfileGeometry.lift): constant 50 — `p20,p50,p80 = np.percentile(d,(20,50,80),axis=1)`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:181 (ProfileGeometry.lift): constant 80 — `p20,p50,p80 = np.percentile(d,(20,50,80),axis=1)`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:183 (ProfileGeometry.lift): constant 0.001 — `return self.to_world(frame,Points(pc)).values, pc, (p80-p20)/np.maximum(p50,1e-3)`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:191 (ProfileGeometry.fov_of): constant 500 — `return 2*np.arctan(500/Kc[1,1]), 2*np.arctan(500/Kc[0,0])`
- `A3.threshold` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:93 (public_fields): compares against 1e-08 — `if (abs(abs(x['axes'][vertical,1])-1) > 1e-8`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:93 (public_fields): constant 1e-08 — `if (abs(abs(x['axes'][vertical,1])-1) > 1e-8`
- `A3.threshold` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:94 (public_fields): compares against 1e-08 — `or np.max(np.abs(x['axes'][horizontal,1])) > 1e-8):`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:94 (public_fields): constant 1e-08 — `or np.max(np.abs(x['axes'][horizontal,1])) > 1e-8):`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:97 (public_fields): identifier degrees — `yaw = int(number(np.degrees(np.arctan2(-direction[2],direction[0])),0))`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:98 (public_fields): constant 180 — `yaw = (yaw + 180) % 360 - 180`
- `A3.constant` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:98 (public_fields): constant 360 — `yaw = (yaw + 180) % 360 - 180`
- `A3.threshold` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:555 (ground): compares against MAX_INSTANCES — `if len(blocks)>MAX_INSTANCES:`

### A4

- response_cites_undeclared_module x6 items ['camera_0', 'ground_0']  {"modules": ["g3t"], "call": "<move from=1 to=9>"}
- `A4.guard` /scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/artifact.py:198 (_patch_native): identifier _guarded — `wrapper = _NATIVE.setdefault(id(original), (original, _guarded(original)))[1]`
- `A4.status_literal` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:226 (BoxRegistry.gap): string 'not seen' — `states=[self.states.get(n,'not seen') for n in names]`
- `A4.status_literal` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:227 (BoxRegistry.gap): string 'not seen' — `for status in ('unresolved','not seen','box unavailable'):`
- `A4.status_literal` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:227 (BoxRegistry.gap): string 'box unavailable' — `for status in ('unresolved','not seen','box unavailable'):`
- `A4.status_literal` /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:518 (ground): string 'not seen' — `else 'not seen' if not entries else None)`

