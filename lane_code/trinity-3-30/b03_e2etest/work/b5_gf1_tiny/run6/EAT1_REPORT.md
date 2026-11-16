# EAT-1 report: eat1.adapters.gf1_tiny:make_reader

Artifact manifest /scratch/jjyeung/orch_n30/b03_e2etest/work/b5_gf1_tiny/artifact/ARTIFACT.json (sha256 a7c029a7acf811ae84ee08268df34d0ebddcc7e85b79d4b9c3df64b1d7c0a562); items 6; mode dynamic; started 2026-11-16T14:59:32Z.

| Clause | Status | Summary |
|---|---|---|
| A1 | PASS | 0 artifact, 7 code, 6 input, 0 outside-artifact data files opened after generate() started |
| A2 | FAIL | model entries per item {1: 6}; 154 tokens fed that neither the model chose nor a registered handler emitted; 3 static findings |
| A3 | FAIL | 15 findings in 18 call-path files {'A3.threshold': 2, 'A3.constant': 10, 'A3.unit_conversion': 3} |
| A4 | FAIL | 4 offender groups (4 static) |
| A5 | PASS | parts {'iii': 'PASS', 'i': 'PASS', 'ii': 'PASS'} |

Overall: **FAIL**

## Per type (A6)

| Type | Items | Call rate | Calls/item | Heads behind response fields | s/item (mean, median, max) |
|---|---|---|---|---|---|
| direct | 2 | 0.000 | 0.00 | - | 0.559, 0.559, 0.687 |
| move | 2 | 1.000 | 1.00 | move: {'pose_head,g3t,gf1': 2} | 1.554, 1.554, 1.766 |
| turn | 2 | 1.000 | 1.00 | turn: {'pose_head,g3t,gf1': 2} | 0.848, 0.848, 0.854 |

## Findings inside registered model classes (informational, 3; not failing)

- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:126 (CameraHead.activate_fov): constant 0.0001
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:126 (CameraHead.activate_fov): constant 0.0002
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/camera_head.py:182 (CameraHead.forward_with_extras): constant 1e-06

## Fixture files excluded from the call path

- /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/tests/test_carrier_c1_final.py

## Offenders by clause (file and line)

### A2

- injected_token x154 items ['move_0', 'move_1', 'turn_0', 'turn_1'] /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:65 consume_cache_tokens {"token": 43, "expected": 42, "position": 135}
- no_call_handler_registered_on_model x4 items ['move_0', 'move_1', 'turn_0', 'turn_1']  {}
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:89 (Row.__init__): response text built outside a torch module method — `self.reserved = [self.tokenizer.convert_tokens_to_ids('<tool_response>'),`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:90 (Row.__init__): response text built outside a torch module method — `self.tokenizer.convert_tokens_to_ids('</tool_response>'), model.carrier_id]`
- `A2.response_outside_model` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:142 (Row._call): response text built outside a torch module method — `wrapped = '\n<tool_response>\n' + text + '\n</tool_response>' if self.ground_layout else '<tool_response>' + text + '</tool_response>'`

### A3

- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:124 (Row._call): compares against MAX_CALL_TOKENS — `if self.active is not None and (tail.endswith('>') or len(ids) - self.active > D.MAX_CALL_TOKENS):`
- `A3.threshold` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:136 (Row._call): compares against max_calls — `if len(self.records) >= self.max_calls:`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:119 (wrap): constant 180 — `return (deg + 180) % 360 - 180 if (deg + 180) % 360 else 180`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:119 (wrap): constant 360 — `return (deg + 180) % 360 - 180 if (deg + 180) % 360 else 180`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:267 (OwnGeometry.pose): identifier yaw_degree — `yaw_degree=round(math.degrees(math.atan2(-level[0][2], level[2][2]))))`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:267 (OwnGeometry.pose): identifier degrees — `yaw_degree=round(math.degrees(math.atan2(-level[0][2], level[2][2]))))`
- `A3.unit_conversion` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_routing.py:303 (OwnGeometry.turn_text): identifier degrees — `turn = wrap(round(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], float(a @ b)))))`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:398 (pose9): constant 518 — `g2c, _ = pose_encoding_to_extri_intri(local[None], (518, 518), 'noT_quaR_FoV', False)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:399 (pose9): constant 518 — `w2g, _ = pose_encoding_to_extri_intri(global_[None], (518, 518), 'absT_quaRy_noFoV', False)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:402 (pose9.lift): constant -2 — `return torch.cat([extri, bottom], -2)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:407 (pose9): constant 1024 — `box = coords.double() / 1024`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_online.py:411 (pose9): constant 1e-06 — `scale = raw[1:, :3].norm(dim=-1).mean().clamp_min(1e-6)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_vendor/vggt/utils/rotation.py:106 (mat_to_quat): constant 9 — `m00, m01, m02, m10, m11, m12, m20, m21, m22 = torch.unbind(matrix.reshape(batch_dim + (9,)), dim=-1)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/g3t_vendor/vggt/utils/rotation.py:135 (mat_to_quat): constant 0.1 — `flr = torch.tensor(0.1).to(dtype=q_abs.dtype, device=q_abs.device)`
- `A3.constant` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/ground_context.py:44 (from_row): constant 32 — `mapping=FrameMap(tuple(indices),rgb_sha256=hashes) if len(indices)==32 else None`

### A4

- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_batch_decode.py:156 (Row.record): string 'error' — `generated_tokens=len(self.ids), errors=sum(r['kind'] == 'error' or r.get('verify_error',False) for r in self.records))`
- `A4.status_literal` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:499 (ground_layout_for): string 'error' — `return trace313.active() or state.ground_backend is not None or state.verify_session is not None or state.rereader is not None or (info['kind'] in ('ground','ga`
- `A4.guard` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:516 (respond_state): identifier fallback — `context.fallback=(lambda name:state.rereader.ground(name,registry)) if state.rereader is not None else (lambda name:heads.ground(name,registry))`
- `A4.guard` /scratch/jjyeung/orch_n30/b03_e2etest/work/nextleg/b5/work/tree_r1/student_pilot/carrier_c1_decode.py:526 (respond_state): identifier fallback — `return respond(call_text,registry,state.geometry,context.fallback,gapper)`

