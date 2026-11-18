# EAT-1 report: eat1.adapters.c8r_tiny:make_reader

Artifact manifest /scratch/jjyeung/orch_n30/review_tree10/work/eatrun/c8r/reader/artifact/ARTIFACT.json (sha256 404432a44ee49d50166cdea0a9995174794d5107260bb84c741487cafe6466c3); items 12; mode dynamic; started 2026-11-18T02:24:37Z.

| Clause | Status | Summary |
|---|---|---|
| A1 | PASS | 1 artifact, 5 code, 12 input, 0 outside-artifact data files opened after generate() started; 0 child-process or reader native calls |
| A2 | FAIL | model entries per item {1: 12}; 494 tokens fed that neither the model chose nor a registered handler emitted; 4 static findings |
| A3 | FAIL | 62 findings in 24 call-path files {'A3.constant': 14, 'A3.threshold': 7, 'A3.reformat': 11, 'A3.unit_conversion': 1, 'A3.table_load': 3, 'A3.data_file': 1, 'A3.module_data': 25} |
| A4 | FAIL | 12 offender groups (8 static) |
| A5 | FAIL | parts {'iii': 'PASS', 'i': 'PASS', 'ii': 'FAIL'} |
| A6 | FAIL | 8 items whose reported calls differ from the responses the registered handler wrote |

Overall: **FAIL**; claim grade (strace, sandbox and perturbation all ran): False

## Per type (A6)

| Type | Items | Call rate | Calls/item | Heads behind response fields | s/item (mean, median, max) |
|---|---|---|---|---|---|
| depth_dist | 2 | 1.000 | 2.00 | camera_points: {'pose_head,depth_head': 2}; distance: {'pose_head,depth_head': 2} | 0.679, 0.679, 0.760 |
| direct | 2 | 0.000 | 0.00 | - | 0.072, 0.072, 0.077 |
| ground | 2 | 1.000 | 1.00 | (unattributed): {'none': 2} | 0.145, 0.145, 0.151 |
| move | 2 | 1.000 | 1.00 | move: {'pose_head': 2} | 0.286, 0.286, 0.294 |
| pose | 2 | 0.000 | 0.00 | - | 0.054, 0.054, 0.055 |
| turn | 2 | 1.000 | 1.00 | turn: {'pose_head': 2} | 0.137, 0.137, 0.158 |

## Fixture files excluded from the call path

- /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/tests/test_carrier_c1_final.py

## Offenders by clause (file and line)

### A2

- injected_token x494 items ['depth_dist_0', 'depth_dist_1', 'ground_0', 'ground_1', 'move_0', 'move_1', 'turn_0', 'turn_1'] /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_decode.py:65 consume_cache_tokens {"token": 43, "expected": 49, "position": 87}
- no_call_handler_registered_on_model x8 items ['depth_dist_0', 'depth_dist_1', 'ground_0', 'ground_1', 'move_0', 'move_1', 'turn_0', 'turn_1']  {}
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:94 (Row.__init__): response text built outside a torch module method — `self.reserved = [self.tokenizer.convert_tokens_to_ids('<tool_response>'),`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:95 (Row.__init__): response text built outside a torch module method — `self.tokenizer.convert_tokens_to_ids('</tool_response>'), model.carrier_id]`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:148 (Row._call): response text built outside a torch module method — `wrapped = '\n<tool_response>\n' + text + '\n</tool_response>' if self.ground_layout else '<tool_response>' + text + '</tool_response>'`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/trace_format/calculator.py:255 (PrintedPointRegistry.execute): response text built outside a torch module method — `"injected_text": "<tool_response>"+text+"</tool_response>"})`

### A3

- `A3.constant` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/camera_head.py:126 (CameraHead.activate_fov): constant 0.0001 — `return 1e-4 + (math.pi - 2e-4) * torch.sigmoid(value)`
- `A3.constant` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/camera_head.py:126 (CameraHead.activate_fov): constant 0.0002 — `return 1e-4 + (math.pi - 2e-4) * torch.sigmoid(value)`
- `A3.constant` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/camera_head.py:182 (CameraHead.forward_with_extras): constant 1e-06 — `raw_grav = F.normalize(grav_pred, dim=-1, eps=1e-6)`
- `A3.threshold` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/camera_head.py:532 (gather_positions): comparison or clamp API positions.clamp_min() — `return hidden[rows, positions.clamp_min(0)]`
- `A3.threshold` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:99 (Row.__init__): compares against attribute state.cap (a configured value) — `self.finish = 'context_exhaustion' if state.cap <= 0 else None`
- `A3.threshold` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:119 (Row.step): compares against attribute self.state.cap (a configured value) — `if self.finish is None and len(self.ids) >= self.state.cap:`
- `A3.reformat` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_routing.py:108 (r2): round() sets precision outside the model — `return round(float(x), 2) + 0.0`
- `A3.reformat` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_routing.py:112 (f2): format spec .2f outside the model — `return f'{r2(x):.2f}'`
- `A3.reformat` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_routing.py:116 (s2): format spec +.2f outside the model — `return f'{r2(x):+.2f}'`
- `A3.reformat` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_routing.py:128 (r8): np.round() sets precision outside the model — `return np.round(np.asarray(a, dtype=np.float64), 8) + 0.0`
- `A3.constant` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_routing.py:128 (r8): constant 8 — `return np.round(np.asarray(a, dtype=np.float64), 8) + 0.0`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_routing.py:312 (OwnGeometry.pose): identifier yaw_degree — `yaw_degree=self.heading('yaw',level) if self.heading is not None else`
- `A3.threshold` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/fixed_readout.py:25 (DepthReadout.forward): comparison or clamp API np.clip() — `points = np.clip(uv[None] + self.stencil.cpu().numpy(), 0, clip[0]/clip[1])`
- `A3.reformat` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/fixed_readout.py:40 (DepthReadout.forward): np.round() sets precision outside the model — `camera = np.round(ray*p30,int(self.camera_precision)) + 0.0`
- `A3.reformat` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/fixed_readout.py:69 (HeadingReadout.forward): round() sets precision outside the model — `return round(math.atan2(-first[0][2],first[2][2])*(int(self.half_circle)/pi))`
- `A3.reformat` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/fixed_readout.py:72 (HeadingReadout.forward): round() sets precision outside the model — `angle=round(math.atan2(a[0]*b[1]-a[1]*b[0],float(a@b))*(int(self.half_circle)/pi))`
- `A3.constant` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/point_depth_head.py:86 (sincos_2d): constant 1000.0 — `freqs = torch.exp(torch.arange(quarter, device=device, dtype=torch.float32) * (-math.log(1000.0) / max(1, quarter)))`
- `A3.constant` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/point_depth_head.py:90 (sincos_2d): combined constant factor 32.0 in 2 * math.pi * grid_y.reshape(-1, 1) * freqs * 16 — `angles_y = 2 * math.pi * grid_y.reshape(-1, 1) * freqs * 16`
- `A3.constant` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/point_depth_head.py:90 (sincos_2d): constant 16 — `angles_y = 2 * math.pi * grid_y.reshape(-1, 1) * freqs * 16`
- `A3.constant` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/point_depth_head.py:91 (sincos_2d): combined constant factor 32.0 in 2 * math.pi * grid_x.reshape(-1, 1) * freqs * 16 — `angles_x = 2 * math.pi * grid_x.reshape(-1, 1) * freqs * 16`
- `A3.constant` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/point_depth_head.py:91 (sincos_2d): constant 16 — `angles_x = 2 * math.pi * grid_x.reshape(-1, 1) * freqs * 16`
- `A3.threshold` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/point_depth_head.py:189 (PointDepthHead.encode): comparison or clamp API fov_hw.float().clamp() — `fov = fov_hw.float().clamp(0.1, math.pi - 0.1)`
- `A3.constant` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/point_depth_head.py:189 (PointDepthHead.encode): constant 0.1 — `fov = fov_hw.float().clamp(0.1, math.pi - 0.1)`
- `A3.constant` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/point_depth_head.py:215 (PointDepthHead.query): constant 1000.0 — `phase_x = uv[..., 0] / 1000.0 * width - 0.5`
- `A3.constant` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/point_depth_head.py:216 (PointDepthHead.query): constant 1000.0 — `phase_y = uv[..., 1] / 1000.0 * height - 0.5`
- `A3.threshold` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/point_depth_head.py:223 (PointDepthHead.query): comparison or clamp API depth.clamp() — `return depth.clamp(max=self.max_depth_m)`
- `A3.constant` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/point_depth_head.py:263 (sample_points): constant 500.0 — `x, y = uv[..., 0] / 500.0 - 1.0, uv[..., 1] / 500.0 - 1.0`
- `A3.constant` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/trace_format/calculator.py:60 (_decimal_context.call): constant 1024 — `with localcontext(Context(prec=1024, rounding=ROUND_HALF_EVEN)):`
- `A3.reformat` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/trace_format/calculator.py:101 (_vec_text): format spec .2f outside the model — `return "(" + ", ".join(f"{x:.2f}" for x in v) + ")"`
- `A3.threshold` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/trace_format/calculator.py:165 (PrintedPointRegistry.register): compares against attribute self.frame_count (a configured value) — `_require(all(type(k) is int and 1 <= k <= self.frame_count for k in (requested_frame, actual_frame)),`
- `A3.reformat` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/trace_format/calculator.py:178 (PrintedPointRegistry.register): format spec .2f outside the model — `public_f1 = _vec_text(point) if heading_defined else partial_f1(point, lambda x: f'{x:.2f}')`
- `A3.reformat` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/trace_format/calculator.py:180 (PrintedPointRegistry.register): format spec .2f outside the model — `f"spread {reliability:.2f}")`
- `A3.reformat` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/trace_format/calculator.py:199 (PrintedPointRegistry.execute): format spec .2f outside the model — `text = f"{result['value']:.2f} m"`
- `A3.table_load` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/trace_format/readout_config.py:6 (load): json.loads() — `return json.loads(Path(__file__).with_suffix('.json').read_text())`
- `A3.table_load` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/trace_format/readout_config.py:6 (load): Path(__file__).with_suffix('.json').read_text() — `return json.loads(Path(__file__).with_suffix('.json').read_text())`
- `A3.data_file` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/trace_format/readout_config.py:6 (load): string '.json' — `return json.loads(Path(__file__).with_suffix('.json').read_text())`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1.py:214 (CarrierC1.geometry_features): reads self.config: instance state number 60 — `self.config`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/camera_head.py:287 (CameraSupervision.carrier_states): reads self.settings: instance state table holding numbers (number 0.02) — `self.settings`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/camera_head.py:312 (CameraSupervision.predict_all): reads self.settings: instance state table holding numbers (number 0.02) — `self.settings`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/decoupled_v.py:104 (features): reads global ANCHORS: module-level table holding numbers (number 6) — `ANCHORS`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/p3_heads.py:86 (PrefixCapture.finish): reads self.batch: instance state table holding numbers (tensor (1, 85)) — `self.batch`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_decode.py:212 (HeadState.geometry): reads self.pose9: instance state array (32, 9) — `self.pose9`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_decode.py:212 (HeadState.geometry): reads self.gravity: instance state array (3,) — `self.gravity`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_routing.py:260 (OwnGeometry._basis): reads global FLIP: module-level array (3, 3) — `FLIP`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:101 (Row.step): reads self.reserved: instance state table holding numbers (number 43) — `self.reserved`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:101 (Row.step): reads self.state: instance state number 85 — `self.state`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:123 (Row._call): reads self.ids: instance state table holding numbers (number 40) — `self.ids`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:123 (Row._call): reads self.state: instance state number 85 — `self.state`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:123 (Row._call): reads self.max_call_tokens: instance state number 96 — `self.max_call_tokens`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:123 (Row._call): reads self.max_calls: instance state number 200 — `self.max_calls`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:123 (Row._call): reads self.registry: instance state number 32 — `self.registry`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_routing.py:316 (OwnGeometry.click): reads global STENCIL: module-level array (25, 2) — `STENCIL`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_routing.py:294 (OwnGeometry.fov): reads self.p: instance state array (32, 9) — `self.p`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/point_depth_head.py:201 (PointDepthHead.query): reads self.min_depth_m: instance state number 0.05 — `self.min_depth_m`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/point_depth_head.py:201 (PointDepthHead.query): reads self.max_depth_m: instance state number 25.0 — `self.max_depth_m`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_routing.py:282 (OwnGeometry.camera): reads self.p: instance state array (32, 9) — `self.p`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:155 (Row.record): reads self.state: instance state number 85 — `self.state`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:155 (Row.record): reads self.ids: instance state table holding numbers (number 40) — `self.ids`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:155 (Row.record): reads self.records: instance state table holding numbers (number 139) — `self.records`
- `A3.module_data` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_routing.py:355 (OwnGeometry.move_text): reads self.down: instance state array (3,) — `self.down`
- ... 2 more in EAT1_REPORT.json

### A4

- reader_error x2 items ['pose_0', 'pose_1']  {"detail": "CallError: bad_frame"}
- answer_not_generated_after_last_response x2 items ['pose_0', 'pose_1']  {"answer": null, "tail": "<pose frame=40>"}
- reported_text_differs_from_generated_sequence x2 items ['pose_0', 'pose_1']  {}
- response_without_head x2 items ['ground_0', 'ground_1']  {"call": "<ground obj=\"chair\">", "response": "error: head_readout"}
- `A4.status_literal` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:164 (Row.record): string 'error' — `generated_tokens=len(self.ids), errors=sum(r['kind'] == 'error' or r.get('verify_error',False) for r in self.records))`
- `A4.except_substitute` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_decode.py:264 (respond): except-handler does not re-raise; a substitute flows on — `if exc.code == 'bad_frame':`
- `A4.except_substitute` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_decode.py:270 (respond): except-handler does not re-raise; a substitute flows on — `return f'error: {exc}', dict(kind='error', code='head_readout')`
- `A4.status_literal` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_decode.py:270 (respond): string 'error: ' — `return f'error: {exc}', dict(kind='error', code='head_readout')`
- `A4.status_literal` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_decode.py:270 (respond): string 'error' — `return f'error: {exc}', dict(kind='error', code='head_readout')`
- `A4.status_literal` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/carrier_c1_decode.py:521 (ground_layout_for): string 'error' — `return trace313.active() or state.ground_backend is not None or state.verify_session is not None or state.rereader is not None or (info['kind'] in ('ground','ga`
- `A4.guard` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/ground_context.py:24 (GroundContext.ground_route): identifier fallback — `return self.fallback`
- `A4.guard` /scratch/jjyeung/orch_n30/review_tree10/work/pkg/work/tree_r1/student_pilot/ground_context.py:28 (GroundContext.ground_route): identifier fallback — `self.fallback = value`

### A5

- perturbed_run_raised x24 items ['pose_0', 'pose_1']  {"module": "depth_head", "seed": 1, "gain": 1.0, "error": "CallError: bad_frame"}

### A6

- reported_calls_differ_from_observed_handler_responses x8 items ['depth_dist_0', 'depth_dist_1', 'ground_0', 'ground_1', 'move_0', 'move_1', 'turn_0', 'turn_1']  {"observed": 0, "reported": 2}

