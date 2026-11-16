# EAT-1 report: eat1.adapters.gf1_tiny:make_reader

Artifact manifest /scratch/jjyeung/orch_n30/b03_e2etest/work/b5_gf1_tiny/artifact/ARTIFACT.json (sha256 a7c029a7acf811ae84ee08268df34d0ebddcc7e85b79d4b9c3df64b1d7c0a562); items 6; mode dynamic; started 2026-11-16T19:14:14Z.

| Clause | Status | Summary |
|---|---|---|
| A1 | PASS | 0 artifact, 7 code, 6 input, 0 outside-artifact data files opened after generate() started; 0 child-process or reader native calls |
| A2 | FAIL | model entries per item {1: 6}; 154 tokens fed that neither the model chose nor a registered handler emitted; 3 static findings |
| A3 | FAIL | 71 findings in 31 call-path files {'A3.constant': 16, 'A3.threshold': 11, 'A3.reformat': 6, 'A3.unit_conversion': 3, 'A3.module_data': 35} |
| A4 | FAIL | 4 offender groups (4 static) |
| A5 | FAIL | parts {'iii': 'PASS', 'i': 'FAIL', 'ii': 'PASS'} |
| A6 | FAIL | 4 items whose reported calls differ from the responses the registered handler wrote |

Overall: **FAIL**; claim grade (strace, sandbox and perturbation all ran): False

## Per type (A6)

| Type | Items | Call rate | Calls/item | Heads behind response fields | s/item (mean, median, max) |
|---|---|---|---|---|---|
| direct | 2 | 0.000 | 0.00 | - | 0.135, 0.135, 0.137 |
| move | 2 | 1.000 | 1.00 | move: {'pose_head,g3t,gf1': 2} | 0.633, 0.633, 0.663 |
| turn | 2 | 1.000 | 1.00 | turn: {'pose_head,g3t,gf1': 2} | 0.252, 0.252, 0.256 |

## Fixture files excluded from the call path

- /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/tests/test_carrier_c1_final.py
- /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/tests/test_gf1.py

## Offenders by clause (file and line)

### A2

- injected_token x154 items ['move_0', 'move_1', 'turn_0', 'turn_1'] /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:65 consume_cache_tokens {"token": 43, "expected": 42, "position": 135}
- no_call_handler_registered_on_model x4 items ['move_0', 'move_1', 'turn_0', 'turn_1']  {}
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:89 (Row.__init__): response text built outside a torch module method — `self.reserved = [self.tokenizer.convert_tokens_to_ids('<tool_response>'),`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:90 (Row.__init__): response text built outside a torch module method — `self.tokenizer.convert_tokens_to_ids('</tool_response>'), model.carrier_id]`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:142 (Row._call): response text built outside a torch module method — `wrapped = '\n<tool_response>\n' + text + '\n</tool_response>' if self.ground_layout else '<tool_response>' + text + '</tool_response>'`

### A3

- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:126 (CameraHead.activate_fov): constant 0.0001 — `return 1e-4 + (math.pi - 2e-4) * torch.sigmoid(value)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:126 (CameraHead.activate_fov): constant 0.0002 — `return 1e-4 + (math.pi - 2e-4) * torch.sigmoid(value)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:182 (CameraHead.forward_with_extras): constant 1e-06 — `raw_grav = F.normalize(grav_pred, dim=-1, eps=1e-6)`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:532 (gather_positions): comparison or clamp API positions.clamp_min() — `return hidden[rows, positions.clamp_min(0)]`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:94 (Row.__init__): compares against attribute state.cap (a configured value) — `self.finish = 'context_exhaustion' if state.cap <= 0 else None`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:114 (Row.step): compares against attribute self.state.cap (a configured value) — `if self.finish is None and len(self.ids) >= self.state.cap:`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:124 (Row._call): compares against MAX_CALL_TOKENS — `if self.active is not None and (tail.endswith('>') or len(ids) - self.active > D.MAX_CALL_TOKENS):`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:136 (Row._call): compares against max_calls — `if len(self.records) >= self.max_calls:`
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
- `A3.reformat` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:303 (OwnGeometry.turn_text): round() sets precision outside the model — `turn = wrap(round(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], float(a @ b)))))`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:303 (OwnGeometry.turn_text): identifier degrees — `turn = wrap(round(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], float(a @ b)))))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:398 (pose9): constant 518 — `g2c, _ = pose_encoding_to_extri_intri(local[None], (518, 518), 'noT_quaR_FoV', False)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:399 (pose9): constant 518 — `w2g, _ = pose_encoding_to_extri_intri(global_[None], (518, 518), 'absT_quaRy_noFoV', False)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:402 (pose9.lift): constant -2 — `return torch.cat([extri, bottom], -2)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:407 (pose9): constant 1024 — `box = coords.double() / 1024`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:411 (pose9): comparison or clamp API raw[1:, :3].norm(dim=-1).mean().clamp_mi() — `scale = raw[1:, :3].norm(dim=-1).mean().clamp_min(1e-6)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:411 (pose9): constant 1e-06 — `scale = raw[1:, :3].norm(dim=-1).mean().clamp_min(1e-6)`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_vendor/vggt/layers/block.py:84 (Block.forward): compares against attribute self.sample_drop_ratio (a configured value) — `if self.training and self.sample_drop_ratio > 0.1:`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_vendor/vggt/layers/block.py:84 (Block.forward): constant 0.1 — `if self.training and self.sample_drop_ratio > 0.1:`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_vendor/vggt/layers/block.py:92 (Block.forward): compares against attribute self.sample_drop_ratio (a configured value) — `elif self.training and self.sample_drop_ratio > 0.0:`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_vendor/vggt/utils/rotation.py:106 (mat_to_quat): constant 9 — `m00, m01, m02, m10, m11, m12, m20, m21, m22 = torch.unbind(matrix.reshape(batch_dim + (9,)), dim=-1)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_vendor/vggt/utils/rotation.py:135 (mat_to_quat): constant 0.1 — `flr = torch.tensor(0.1).to(dtype=q_abs.dtype, device=q_abs.device)`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_vendor/vggt/utils/rotation.py:140 (mat_to_quat): compares against 0.5 — `out = quat_candidates[F.one_hot(q_abs.argmax(dim=-1), num_classes=4) > 0.5, :].reshape(batch_dim + (4,))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/gf1.py:58 (area_pool.weights): constant 1024 — `edges = torch.linspace(0, 1024, source + 1, device=features.device)`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/gf1.py:60 (area_pool.weights): comparison or clamp API (torch.minimum(bounds[1:, None], edges[N() — `return (torch.minimum(bounds[1:, None], edges[None, 1:]) -`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/gf1.py:127 (Fusion.inject.visual_hook): comparison or clamp API visual.float().square().mean().sqrt().cl() — `visual.float().square().mean().sqrt().clamp_min(1e-12))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/ground_context.py:44 (from_row): constant 32 — `mapping=FrameMap(tuple(indices),rgb_sha256=hashes) if len(indices)==32 else None`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1.py:206 (CarrierC1.geometry_features): reads self.geometry_online: instance state table holding numbers (number 16) — `self.geometry_online`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1.py:206 (CarrierC1.geometry_features): reads self.geometry_runtime: instance state table holding numbers (number 0.25) — `self.geometry_runtime`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:308 (G3TEncoder.forward): reads self.image_size: instance state number 28 — `self.image_size`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:308 (G3TEncoder.forward): reads self.settings: instance state table holding numbers (number 16) — `self.settings`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:295 (G3TEncoder._forward): reads self.settings: instance state table holding numbers (number 16) — `self.settings`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:291 (G3TEncoder._autocast): reads self.settings: instance state table holding numbers (number 16) — `self.settings`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:247 (G3TEncoder._lean): reads self.settings: instance state table holding numbers (number 16) — `self.settings`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:232 (G3TEncoder._call): reads self.settings: instance state table holding numbers (number 16) — `self.settings`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_vendor/vggt/layers/patch_embed.py:65 (PatchEmbed.forward): reads self.patch_size: instance state table holding numbers (number 14) — `self.patch_size`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_vendor/vggt/layers/patch_embed.py:65 (PatchEmbed.forward): reads self.embed_dim: instance state number 16 — `self.embed_dim`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_vendor/vggt/layers/attention.py:50 (Attention.forward): reads self.head_dim: instance state number 8 — `self.head_dim`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_vendor/vggt/layers/attention.py:50 (Attention.forward): reads self.scale: instance state number 0.3535533905932738 — `self.scale`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_vendor/vggt/layers/rope.py:86 (RotaryPositionEmbedding2D._compute_frequency_components): reads self.base_frequency: instance state number 100 — `self.base_frequency`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:281 (G3TEncoder._camera): reads self.settings: instance state table holding numbers (number 16) — `self.settings`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1.py:283 (CarrierC1.patch_injection): reads self.geometry_online: instance state table holding numbers (number 16) — `self.geometry_online`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1.py:283 (CarrierC1.patch_injection): reads self.gx_metrics: instance state table holding numbers (number 64) — `self.gx_metrics`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/gf1.py:105 (Fusion.inject): reads self.settings: instance state table holding numbers (number 16) — `self.settings`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1.py:296 (CarrierC1.carrier_embeddings): reads self.gx_metrics: instance state table holding numbers (number 64) — `self.gx_metrics`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/gf1.py:89 (Fusion.forward): reads self.settings: instance state table holding numbers (number 16) — `self.settings`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:287 (CameraSupervision.carrier_states): reads self.settings: instance state table holding numbers (number 0.02) — `self.settings`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:312 (CameraSupervision.predict_all): reads self.settings: instance state table holding numbers (number 0.02) — `self.settings`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:210 (HeadState.geometry): reads self.pose9: instance state array (32, 9) — `self.pose9`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:210 (HeadState.geometry): reads self.gravity: instance state array (3,) — `self.gravity`
- `A3.module_data` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:225 (OwnGeometry.__init__): reads global FLIP: module-level array (3, 3) — `FLIP`
- ... 11 more in EAT1_REPORT.json

### A4

- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:156 (Row.record): string 'error' — `generated_tokens=len(self.ids), errors=sum(r['kind'] == 'error' or r.get('verify_error',False) for r in self.records))`
- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:499 (ground_layout_for): string 'error' — `return trace313.active() or state.ground_backend is not None or state.verify_session is not None or state.rereader is not None or (info['kind'] in ('ground','ga`
- `A4.guard` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:516 (respond_state): identifier fallback — `context.fallback=(lambda name:state.rereader.ground(name,registry)) if state.rereader is not None else (lambda name:heads.ground(name,registry))`
- `A4.guard` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:526 (respond_state): identifier fallback — `return respond(call_text,registry,state.geometry,context.fallback,gapper)`

### A5

- sandboxed_run_failed x1 items None  {"returncode": 1, "stderr_tail": "ux-x86_64-gnu/lib/python3.12/pathlib.py\", line 1027, in read_text\n    with self.open(mode='r', encoding=encoding, errors=errors) as f:\n         ^^^^^^^^^^^^^^^^^^^

### A6

- reported_calls_differ_from_observed_handler_responses x4 items ['move_0', 'move_1', 'turn_0', 'turn_1']  {"observed": 0, "reported": 1}

