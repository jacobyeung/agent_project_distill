# EAT-1 report: eat1.adapters.c8r_tiny:make_reader

Artifact manifest /scratch/jjyeung/orch_n30/b03_e2etest/work/c8r_tiny/artifact/ARTIFACT.json (sha256 f4ad61dd695fd5a1e862f5eae787ebf61cdc7fe513f0fb79348b249265855f45); items 12; mode dynamic; started 2026-11-16T14:56:48Z.

| Clause | Status | Summary |
|---|---|---|
| A1 | PASS | 0 artifact, 5 code, 12 input, 0 outside-artifact data files opened after generate() started |
| A2 | FAIL | model entries per item {1: 12}; 530 tokens fed that neither the model chose nor a registered handler emitted; 4 static findings |
| A3 | FAIL | 28 findings in 17 call-path files {'A3.threshold': 3, 'A3.constant': 22, 'A3.unit_conversion': 3} |
| A4 | FAIL | 11 offender groups (10 static) |
| A5 | PASS | parts {'iii': 'PASS', 'i': 'PASS', 'ii': 'PASS'} |

Overall: **FAIL**

## Per type (A6)

| Type | Items | Call rate | Calls/item | Heads behind response fields | s/item (mean, median, max) |
|---|---|---|---|---|---|
| depth_dist | 2 | 1.000 | 2.00 | camera_points: {'pose_head,depth_head': 2}; distance: {'pose_head,depth_head': 2} | 0.879, 0.879, 0.928 |
| direct | 2 | 0.000 | 0.00 | - | 0.085, 0.085, 0.085 |
| ground | 2 | 1.000 | 1.00 | (unattributed): {'none': 2} | 0.173, 0.173, 0.181 |
| move | 2 | 1.000 | 1.00 | move: {'pose_head': 2} | 0.363, 0.363, 0.376 |
| pose | 2 | 1.000 | 1.00 | (unattributed): {'none': 2} | 0.179, 0.179, 0.180 |
| turn | 2 | 1.000 | 1.00 | turn: {'pose_head': 2} | 0.185, 0.185, 0.189 |

## Findings inside registered model classes (informational, 6; not failing)

- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/camera_head.py:126 (CameraHead.activate_fov): constant 0.0001
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/camera_head.py:126 (CameraHead.activate_fov): constant 0.0002
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/camera_head.py:182 (CameraHead.forward_with_extras): constant 1e-06
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/point_depth_head.py:189 (PointDepthHead.encode): constant 0.1
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/point_depth_head.py:215 (PointDepthHead.query): constant 1000.0
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/point_depth_head.py:216 (PointDepthHead.query): constant 1000.0

## Fixture files excluded from the call path

- /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/tests/test_carrier_c1_final.py

## Offenders by clause (file and line)

### A2

- injected_token x530 items ['depth_dist_0', 'depth_dist_1', 'ground_0', 'ground_1', 'move_0', 'move_1', 'pose_0', 'pose_1', 'turn_0', 'turn_1'] /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_decode.py:65 consume_cache_tokens {"token": 43, "expected": 49, "position": 87}
- no_call_handler_registered_on_model x10 items ['depth_dist_0', 'depth_dist_1', 'ground_0', 'ground_1', 'move_0', 'move_1', 'pose_0', 'pose_1', 'turn_0', 'turn_1']  {}
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_batch_decode.py:89 (Row.__init__): response text built outside a torch module method — `self.reserved = [self.tokenizer.convert_tokens_to_ids('<tool_response>'),`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_batch_decode.py:90 (Row.__init__): response text built outside a torch module method — `self.tokenizer.convert_tokens_to_ids('</tool_response>'), model.carrier_id]`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_batch_decode.py:142 (Row._call): response text built outside a torch module method — `wrapped = '\n<tool_response>\n' + text + '\n</tool_response>' if self.ground_layout else '<tool_response>' + text + '</tool_response>'`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/p3_printed_calculator.py:242 (PrintedPointRegistry.execute): response text built outside a torch module method — `"injected_text": "<tool_response>"+text+"</tool_response>"})`

### A3

- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_batch_decode.py:124 (Row._call): compares against MAX_CALL_TOKENS — `if self.active is not None and (tail.endswith('>') or len(ids) - self.active > D.MAX_CALL_TOKENS):`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_batch_decode.py:136 (Row._call): compares against max_calls — `if len(self.records) >= self.max_calls:`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_decode.py:204 (HeadState.depth): constant 500.0 — `uv = torch.full((self.depth_map.shape[0], len(points), 2), 500., device=self.depth_map.device)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_routing.py:119 (wrap): constant 180 — `return (deg + 180) % 360 - 180 if (deg + 180) % 360 else 180`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_routing.py:119 (wrap): constant 360 — `return (deg + 180) % 360 - 180 if (deg + 180) % 360 else 180`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_routing.py:264 (OwnGeometry.pose): identifier yaw_degree — `yaw_degree=round(math.degrees(math.atan2(-level[0][2], level[2][2]))))`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_routing.py:264 (OwnGeometry.pose): identifier degrees — `yaw_degree=round(math.degrees(math.atan2(-level[0][2], level[2][2]))))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_routing.py:274 (OwnGeometry.click): constant 999.9 — `points = np.clip(uv[None] + STENCIL, 0, 999.9)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_routing.py:278 (OwnGeometry.click): constant 20 — `p20, p30, p50, p80 = (np.percentile(values, q) for q in (20, 30, 50, 80))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_routing.py:278 (OwnGeometry.click): constant 30 — `p20, p30, p50, p80 = (np.percentile(values, q) for q in (20, 30, 50, 80))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_routing.py:278 (OwnGeometry.click): constant 50 — `p20, p30, p50, p80 = (np.percentile(values, q) for q in (20, 30, 50, 80))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_routing.py:278 (OwnGeometry.click): constant 80 — `p20, p30, p50, p80 = (np.percentile(values, q) for q in (20, 30, 50, 80))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_routing.py:279 (OwnGeometry.click): constant 0.001 — `spread = (p80 - p20) / max(p50, 1e-3)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_routing.py:281 (OwnGeometry.click): constant 500 — `ray = np.array([(uv[0] / 500 - 1) * math.tan(horizontal / 2), (uv[1] / 500 - 1) * math.tan(vertical / 2), 1.])`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_routing.py:300 (OwnGeometry.turn_text): identifier degrees — `turn = wrap(round(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], float(a @ b)))))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/decoupled_v.py:111 (features): constant 33 — `all_frames = anchors == list(range(1, 33))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/decoupled_v.py:116 (features): constant 33 — `allowed = tuple(range(1, 33)) if allow_short else (32,)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/decoupled_v.py:116 (features): constant 32 — `allowed = tuple(range(1, 33)) if allow_short else (32,)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/decoupled_v.py:120 (features): constant 16 — `if n != 16 or single_slot:`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/ground_context.py:44 (from_row): constant 32 — `mapping=FrameMap(tuple(indices),rgb_sha256=hashes) if len(indices)==32 else None`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/p3_printed_calculator.py:55 (_decimal_context.call): constant 1024 — `with localcontext(Context(prec=1024, rounding=ROUND_HALF_EVEN)):`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/p3_printed_calculator.py:159 (PrintedPointRegistry.register): compares against 32 — `_require(all(type(k) is int and 1 <= k <= 32 for k in (requested_frame, actual_frame)),`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/p3_printed_calculator.py:159 (PrintedPointRegistry.register): constant 32 — `_require(all(type(k) is int and 1 <= k <= 32 for k in (requested_frame, actual_frame)),`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/point_depth_head.py:86 (sincos_2d): constant 1000.0 — `freqs = torch.exp(torch.arange(quarter, device=device, dtype=torch.float32) * (-math.log(1000.0) / max(1, quarter)))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/point_depth_head.py:90 (sincos_2d): constant 16 — `angles_y = 2 * math.pi * grid_y.reshape(-1, 1) * freqs * 16`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/point_depth_head.py:91 (sincos_2d): constant 16 — `angles_x = 2 * math.pi * grid_x.reshape(-1, 1) * freqs * 16`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/point_depth_head.py:262 (sample_points): constant 500.0 — `x, y = uv[..., 0] / 500.0 - 1.0, uv[..., 1] / 500.0 - 1.0`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/point_depth_head.py:313 (vit_grids_by_row): constant 5 — `result.append(units.permute(0, 1, 3, 2, 4, 5).reshape(t, h, w, dim))`

### A4

- response_without_head x4 items ['ground_0', 'ground_1', 'pose_0', 'pose_1']  {"call": "<pose frame=40>", "response": "error: bad_frame"}
- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_batch_decode.py:156 (Row.record): string 'error' — `generated_tokens=len(self.ids), errors=sum(r['kind'] == 'error' or r.get('verify_error',False) for r in self.records))`
- `A4.except_substitute` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_decode.py:244 (respond): except-handler returns a substitute — `return f'error: {exc.code}', dict(kind='error', code=exc.code)`
- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_decode.py:244 (respond): string 'error: ' — `return f'error: {exc.code}', dict(kind='error', code=exc.code)`
- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_decode.py:244 (respond): string 'error' — `return f'error: {exc.code}', dict(kind='error', code=exc.code)`
- `A4.except_substitute` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_decode.py:248 (respond): except-handler returns a substitute — `return f'error: {exc}', dict(kind='error', code='head_readout')`
- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_decode.py:248 (respond): string 'error: ' — `return f'error: {exc}', dict(kind='error', code='head_readout')`
- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_decode.py:248 (respond): string 'error' — `return f'error: {exc}', dict(kind='error', code='head_readout')`
- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_decode.py:499 (ground_layout_for): string 'error' — `return trace313.active() or state.ground_backend is not None or state.verify_session is not None or state.rereader is not None or (info['kind'] in ('ground','ga`
- `A4.guard` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_decode.py:516 (respond_state): identifier fallback — `context.fallback=(lambda name:state.rereader.ground(name,registry)) if state.rereader is not None else (lambda name:heads.ground(name,registry))`
- `A4.guard` /scratch/jjyeung/orch_n30/b03_e2etest/work/audit_copies/tree_b01ce449/student_pilot/carrier_c1_decode.py:526 (respond_state): identifier fallback — `return respond(call_text,registry,state.geometry,context.fallback,gapper)`

