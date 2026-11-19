# EAT-1 report: eat1.adapters.c8r_tiny:make_reader

Artifact manifest /scratch/jjyeung/orch_n30/b03_e2etest/work/b5_tiny/artifact/ARTIFACT.json (sha256 4375cf9c85dce9858ecce35f8d97bc98b643c33aaca66bd777af11d0c1bcce14); items 12; mode dynamic; started 2026-11-16T20:36:03Z.

| Clause | Status | Summary |
|---|---|---|
| A1 | PASS | 0 artifact, 5 code, 12 input, 0 outside-artifact data files opened after generate() started; 0 child-process or reader native calls |
| A2 | FAIL | model entries per item {1: 12}; 530 tokens fed that neither the model chose nor a registered handler emitted; 4 static findings |
| A3 | FAIL | 74 findings in 21 call-path files {'A3.constant': 30, 'A3.threshold': 9, 'A3.reformat': 9, 'A3.unit_conversion': 3, 'A3.module_data': 23} |
| A4 | FAIL | 11 offender groups (10 static) |
| A5 | PASS | parts {'iii': 'PASS', 'i': 'PASS', 'ii': 'PASS'} |
| A6 | FAIL | 10 items whose reported calls differ from the responses the registered handler wrote |

Overall: **FAIL**; claim grade (strace, sandbox and perturbation all ran): False

## Per type (A6)

| Type | Items | Call rate | Calls/item | Heads behind response fields | s/item (mean, median, max) |
|---|---|---|---|---|---|
| depth_dist | 2 | 1.000 | 2.00 | camera_points: {'pose_head,depth_head': 2}; distance: {'pose_head,depth_head': 2} | 0.860, 0.860, 0.925 |
| direct | 2 | 0.000 | 0.00 | - | 0.070, 0.070, 0.070 |
| ground | 2 | 1.000 | 1.00 | (unattributed): {'none': 2} | 0.161, 0.161, 0.161 |
| move | 2 | 1.000 | 1.00 | move: {'pose_head': 2} | 0.385, 0.385, 0.395 |
| pose | 2 | 1.000 | 1.00 | (unattributed): {'none': 2} | 0.158, 0.158, 0.167 |
| turn | 2 | 1.000 | 1.00 | turn: {'pose_head': 2} | 0.163, 0.163, 0.164 |

## Fixture files excluded from the call path

- /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/tests/test_carrier_c1_final.py

## Offenders by clause (file and line)

### A2

- injected_token x530 items ['depth_dist_0', 'depth_dist_1', 'ground_0', 'ground_1', 'move_0', 'move_1', 'pose_0', 'pose_1', 'turn_0', 'turn_1'] /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:65 consume_cache_tokens {"token": 43, "expected": 49, "position": 87}
- no_call_handler_registered_on_model x10 items ['depth_dist_0', 'depth_dist_1', 'ground_0', 'ground_1', 'move_0', 'move_1', 'pose_0', 'pose_1', 'turn_0', 'turn_1']  {}
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:89 (Row.__init__): response text built outside a torch module method — `self.reserved = [self.tokenizer.convert_tokens_to_ids('<tool_response>'),`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:90 (Row.__init__): response text built outside a torch module method — `self.tokenizer.convert_tokens_to_ids('</tool_response>'), model.carrier_id]`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:142 (Row._call): response text built outside a torch module method — `wrapped = '\n<tool_response>\n' + text + '\n</tool_response>' if self.ground_layout else '<tool_response>' + text + '</tool_response>'`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/p3_printed_calculator.py:242 (PrintedPointRegistry.execute): response text built outside a torch module method — `"injected_text": "<tool_response>"+text+"</tool_response>"})`

### A3

- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:126 (CameraHead.activate_fov): constant 0.0001 — `return 1e-4 + (math.pi - 2e-4) * torch.sigmoid(value)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:126 (CameraHead.activate_fov): constant 0.0002 — `return 1e-4 + (math.pi - 2e-4) * torch.sigmoid(value)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:182 (CameraHead.forward_with_extras): constant 1e-06 — `raw_grav = F.normalize(grav_pred, dim=-1, eps=1e-6)`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:532 (gather_positions): comparison or clamp API positions.clamp_min() — `return hidden[rows, positions.clamp_min(0)]`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:94 (Row.__init__): compares against attribute state.cap (a configured value) — `self.finish = 'context_exhaustion' if state.cap <= 0 else None`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:114 (Row.step): compares against attribute self.state.cap (a configured value) — `if self.finish is None and len(self.ids) >= self.state.cap:`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:124 (Row._call): compares against MAX_CALL_TOKENS — `if self.active is not None and (tail.endswith('>') or len(ids) - self.active > D.MAX_CALL_TOKENS):`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:136 (Row._call): compares against max_calls — `if len(self.records) >= self.max_calls:`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:204 (HeadState.depth): constant 500.0 — `uv = torch.full((self.depth_map.shape[0], len(points), 2), 500., device=self.depth_map.device)`
- `A3.reformat` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:103 (r2): round() sets precision outside the model — `return round(float(x), 2) + 0.0`
- `A3.reformat` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:107 (f2): format spec .2f outside the model — `return f'{r2(x):.2f}'`
- `A3.reformat` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:111 (s2): format spec +.2f outside the model — `return f'{r2(x):+.2f}'`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:119 (wrap): constant 180 — `return (deg + 180) % 360 - 180 if (deg + 180) % 360 else 180`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:119 (wrap): constant 360 — `return (deg + 180) % 360 - 180 if (deg + 180) % 360 else 180`
- `A3.reformat` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:123 (r8): np.round() sets precision outside the model — `return np.round(np.asarray(a, dtype=np.float64), 8) + 0.0`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:123 (r8): constant 8 — `return np.round(np.asarray(a, dtype=np.float64), 8) + 0.0`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:267 (OwnGeometry.pose): identifier yaw_degree — `yaw_degree=round(math.degrees(math.atan2(-level[0][2], level[2][2]))))`
- `A3.reformat` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:267 (OwnGeometry.pose): round() sets precision outside the model — `yaw_degree=round(math.degrees(math.atan2(-level[0][2], level[2][2]))))`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:267 (OwnGeometry.pose): identifier degrees — `yaw_degree=round(math.degrees(math.atan2(-level[0][2], level[2][2]))))`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:277 (OwnGeometry.click): comparison or clamp API np.clip() — `points = np.clip(uv[None] + STENCIL, 0, 999.9)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:277 (OwnGeometry.click): constant 999.9 — `points = np.clip(uv[None] + STENCIL, 0, 999.9)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:281 (OwnGeometry.click): constant 20 — `p20, p30, p50, p80 = (np.percentile(values, q) for q in (20, 30, 50, 80))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:281 (OwnGeometry.click): constant 30 — `p20, p30, p50, p80 = (np.percentile(values, q) for q in (20, 30, 50, 80))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:281 (OwnGeometry.click): constant 50 — `p20, p30, p50, p80 = (np.percentile(values, q) for q in (20, 30, 50, 80))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:281 (OwnGeometry.click): constant 80 — `p20, p30, p50, p80 = (np.percentile(values, q) for q in (20, 30, 50, 80))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:282 (OwnGeometry.click): constant 0.001 — `spread = (p80 - p20) / max(p50, 1e-3)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:284 (OwnGeometry.click): constant 500 — `ray = np.array([(uv[0] / 500 - 1) * math.tan(horizontal / 2), (uv[1] / 500 - 1) * math.tan(vertical / 2), 1.])`
- `A3.reformat` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:303 (OwnGeometry.turn_text): round() sets precision outside the model — `turn = wrap(round(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], float(a @ b)))))`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:303 (OwnGeometry.turn_text): identifier degrees — `turn = wrap(round(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], float(a @ b)))))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/decoupled_v.py:111 (features): constant 33 — `all_frames = anchors == list(range(1, 33))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/decoupled_v.py:116 (features): constant 33 — `allowed = tuple(range(1, 33)) if allow_short else (32,)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/decoupled_v.py:116 (features): constant 32 — `allowed = tuple(range(1, 33)) if allow_short else (32,)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/decoupled_v.py:120 (features): constant 16 — `if n != 16 or single_slot:`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/ground_context.py:44 (from_row): constant 32 — `mapping=FrameMap(tuple(indices),rgb_sha256=hashes) if len(indices)==32 else None`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/p3_printed_calculator.py:55 (_decimal_context.call): constant 1024 — `with localcontext(Context(prec=1024, rounding=ROUND_HALF_EVEN)):`
- `A3.reformat` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/p3_printed_calculator.py:96 (_vec_text): format spec .2f outside the model — `return "(" + ", ".join(f"{x:.2f}" for x in v) + ")"`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/p3_printed_calculator.py:159 (PrintedPointRegistry.register): compares against 32.0 — `_require(all(type(k) is int and 1 <= k <= 32 for k in (requested_frame, actual_frame)),`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/p3_printed_calculator.py:159 (PrintedPointRegistry.register): constant 32 — `_require(all(type(k) is int and 1 <= k <= 32 for k in (requested_frame, actual_frame)),`
- `A3.reformat` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/p3_printed_calculator.py:172 (PrintedPointRegistry.register): format spec .2f outside the model — `f"spread {reliability:.2f}")`
- `A3.reformat` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/p3_printed_calculator.py:189 (PrintedPointRegistry.execute): format spec .2f outside the model — `text = f"{result['value']:.2f} m"`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/point_depth_head.py:86 (sincos_2d): constant 1000.0 — `freqs = torch.exp(torch.arange(quarter, device=device, dtype=torch.float32) * (-math.log(1000.0) / max(1, quarter)))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/point_depth_head.py:90 (sincos_2d): combined constant factor 32.0 in 2 * math.pi * grid_y.reshape(-1, 1) * freqs * 16 — `angles_y = 2 * math.pi * grid_y.reshape(-1, 1) * freqs * 16`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/point_depth_head.py:90 (sincos_2d): constant 16 — `angles_y = 2 * math.pi * grid_y.reshape(-1, 1) * freqs * 16`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/point_depth_head.py:91 (sincos_2d): combined constant factor 32.0 in 2 * math.pi * grid_x.reshape(-1, 1) * freqs * 16 — `angles_x = 2 * math.pi * grid_x.reshape(-1, 1) * freqs * 16`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/point_depth_head.py:91 (sincos_2d): constant 16 — `angles_x = 2 * math.pi * grid_x.reshape(-1, 1) * freqs * 16`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/point_depth_head.py:189 (PointDepthHead.encode): comparison or clamp API fov_hw.float().clamp() — `fov = fov_hw.float().clamp(0.1, math.pi - 0.1)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/point_depth_head.py:189 (PointDepthHead.encode): constant 0.1 — `fov = fov_hw.float().clamp(0.1, math.pi - 0.1)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/point_depth_head.py:215 (PointDepthHead.query): constant 1000.0 — `phase_x = uv[..., 0] / 1000.0 * width - 0.5`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/point_depth_head.py:216 (PointDepthHead.query): constant 1000.0 — `phase_y = uv[..., 1] / 1000.0 * height - 0.5`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/point_depth_head.py:223 (PointDepthHead.query): comparison or clamp API depth.clamp() — `return depth.clamp(max=self.max_depth_m)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/point_depth_head.py:262 (sample_points): constant 500.0 — `x, y = uv[..., 0] / 500.0 - 1.0, uv[..., 1] / 500.0 - 1.0`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1.py:206 (CarrierC1.geometry_features): reads self.config: instance state number 60 — `self.config`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:287 (CameraSupervision.carrier_states): reads self.settings: instance state table holding numbers (number 0.02) — `self.settings`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:312 (CameraSupervision.predict_all): reads self.settings: instance state table holding numbers (number 0.02) — `self.settings`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/decoupled_v.py:104 (features): reads global ANCHORS: module-level table holding numbers (number 6) — `ANCHORS`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/p3_heads.py:86 (PrefixCapture.finish): reads self.batch: instance state table holding numbers (tensor (1, 85)) — `self.batch`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:210 (HeadState.geometry): reads self.pose9: instance state array (32, 9) — `self.pose9`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:210 (HeadState.geometry): reads self.gravity: instance state array (3,) — `self.gravity`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:225 (OwnGeometry.__init__): reads global FLIP: module-level array (3, 3) — `FLIP`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:96 (Row.step): reads self.reserved: instance state table holding numbers (number 43) — `self.reserved`
- ... 14 more in EAT1_REPORT.json

### A4

- response_without_head x4 items ['ground_0', 'ground_1', 'pose_0', 'pose_1']  {"call": "<pose frame=40>", "response": "error: bad_frame"}
- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:156 (Row.record): string 'error' — `generated_tokens=len(self.ids), errors=sum(r['kind'] == 'error' or r.get('verify_error',False) for r in self.records))`
- `A4.except_substitute` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:244 (respond): except-handler does not re-raise; a substitute flows on — `return f'error: {exc.code}', dict(kind='error', code=exc.code)`
- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:244 (respond): string 'error: ' — `return f'error: {exc.code}', dict(kind='error', code=exc.code)`
- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:244 (respond): string 'error' — `return f'error: {exc.code}', dict(kind='error', code=exc.code)`
- `A4.except_substitute` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:248 (respond): except-handler does not re-raise; a substitute flows on — `return f'error: {exc}', dict(kind='error', code='head_readout')`
- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:248 (respond): string 'error: ' — `return f'error: {exc}', dict(kind='error', code='head_readout')`
- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:248 (respond): string 'error' — `return f'error: {exc}', dict(kind='error', code='head_readout')`
- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:499 (ground_layout_for): string 'error' — `return trace313.active() or state.ground_backend is not None or state.verify_session is not None or state.rereader is not None or (info['kind'] in ('ground','ga`
- `A4.guard` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:516 (respond_state): identifier fallback — `context.fallback=(lambda name:state.rereader.ground(name,registry)) if state.rereader is not None else (lambda name:heads.ground(name,registry))`
- `A4.guard` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:526 (respond_state): identifier fallback — `return respond(call_text,registry,state.geometry,context.fallback,gapper)`

### A6

- reported_calls_differ_from_observed_handler_responses x10 items ['depth_dist_0', 'depth_dist_1', 'ground_0', 'ground_1', 'move_0', 'move_1', 'pose_0', 'pose_1', 'turn_0', 'turn_1']  {"observed": 0, "reported": 2}

