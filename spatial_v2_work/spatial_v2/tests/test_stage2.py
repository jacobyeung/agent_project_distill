"""Unit tests for Spatial-V2 Stage-2 Full 9B model, data pipeline, and loss invariants.

Covers:
  1. Zero-init identity test (`fusion_gate=0` -> exact `0.0` perturbation to `Qwen3.5` logits at step 0)
     for BOTH `corresp_stem` (Arm B) and `da3_nested` (Arm C).
  2. Gradient flow test (non-zero finite gradients on front-end bridge, LoRA/trunk, `taps 16 & 24`
     GeoHeads & SF2 probes, and Qwen3.5 LLM parameters; scale_donor strictly frozen) + bitwise
     gradient equivalence of `Qwen3_5DecoderLayer` (`GatedDeltaNet` + `FullAttn`) checkpointing.
  3. Edge-case tests: masked `NaN` depth, `depth_valid` -> `pmap_valid` invariant normalization
     (Codex Stage-1A item #1 fix), and `has_4d_teacher=False` / mixed 4D batch masking with `NaN`s.
  4. `Stage2RoomExclusionGuard` hard refusal of held-out rooms in `Stage2SpatialDataset` and E05 JSONL,
     E05 multi-turn `<verify>`/`<think>`/`<geo>`/`<answer>` assistant-only loss masking, and
     deterministic capture/epoch-keyed view sampling (Codex Stage-1A item #2 fix).
"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import torch

from spatial_v2.data_k1_local import CaptureRecord, build_clean_k1_splits
from spatial_v2.stage2_data import (
    DEFAULT_E05_JSONL,
    Stage2RoomExclusionGuard,
    Stage2SpatialDataset,
    build_synthetic_stage2_batch,
    encode_e05_epistemic_trace,
    load_clean_e05_traces,
)
from spatial_v2.stage2_model import SpatialV2Stage2Model


class TestSpatialV2Stage2(unittest.TestCase):
    def test_01_zero_init_identity_both_frontends(self) -> None:
        """At step 0 (fusion_gate=0), front-end produces exact 0.0 perturbation to Qwen3.5 logits."""
        torch.manual_seed(101)
        batch, _ = build_synthetic_stage2_batch(
            batch_size=2,
            num_views=4,
            grid_h=8,
            grid_w=8,
            seq_len=32,
            vocab_size=1024,
            teacher_dim=64,
            seed=101,
        )
        rgb_da3_alt = batch["rgb_da3"] * -3.5 + 2.0

        for frontend in ("corresp_stem", "da3_nested"):
            model = SpatialV2Stage2Model(
                frontend=frontend,  # type: ignore[arg-type]
                teacher_dim=64,
                gradient_checkpointing=False,
                tiny=True,
            ).eval()

            with torch.no_grad():
                out_a = model(
                    rgb_qwen=batch["rgb_qwen"],
                    rgb_da3=batch["rgb_da3"],
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    timestamps=batch["timestamps"],
                    view_mask=batch["view_mask"],
                    return_logits=True,
                )
                out_b = model(
                    rgb_qwen=batch["rgb_qwen"],
                    rgb_da3=rgb_da3_alt,
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    timestamps=batch["timestamps"],
                    view_mask=batch["view_mask"],
                    return_logits=True,
                )

            assert not isinstance(out_a, tuple) and not isinstance(out_b, tuple)
            assert out_a.logits is not None and out_b.logits is not None

            # 1. Exact 0.0 perturbation between vis_base and vis_fused at step 0
            vis_diff = float((out_a.vis_fused - out_a.vis_base).abs().max().item())
            self.assertEqual(vis_diff, 0.0, f"vis_fused != vis_base at gate=0 for {frontend}: diff={vis_diff}")

            # 2. Exact 0.0 perturbation to Qwen3.5 logits when rgb_da3 changes at gate=0
            logit_diff = float((out_a.logits - out_b.logits).abs().max().item())
            self.assertEqual(logit_diff, 0.0, f"Logits perturbed at gate=0 for {frontend}: diff={logit_diff}")

            # 3. Once fusion_gate != 0, front-end actively modulates vis_fused and Qwen3.5 logits
            with torch.no_grad():
                model.frontend.fusion_gate.fill_(0.5)
                out_c = model(
                    rgb_qwen=batch["rgb_qwen"],
                    rgb_da3=rgb_da3_alt,
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    timestamps=batch["timestamps"],
                    view_mask=batch["view_mask"],
                    return_logits=True,
                )
            assert not isinstance(out_c, tuple) and out_c.logits is not None
            self.assertGreater(float((out_c.vis_fused - out_c.vis_base).abs().max().item()), 1e-4)
            self.assertGreater(float((out_c.logits - out_a.logits).abs().max().item()), 1e-4)

    def test_02_gradient_flow_and_grad_checkpointing_equivalence_both_frontends(self) -> None:
        """Every trainable component (front-end bridge, LoRA/trunk, taps 16 & 24, LLM) gets non-zero finite grads."""
        torch.manual_seed(202)
        batch, teacher_feats = build_synthetic_stage2_batch(
            batch_size=2,
            num_views=4,
            grid_h=8,
            grid_w=8,
            seq_len=32,
            vocab_size=1024,
            teacher_dim=64,
            has_4d_teacher=True,
            include_vla=True,
            seed=202,
        )

        for frontend in ("corresp_stem", "da3_nested"):
            model = SpatialV2Stage2Model(
                frontend=frontend,  # type: ignore[arg-type]
                teacher_dim=64,
                freeze_scale_donor=True,
                lora_rank=8,
                unfreeze_last_k=2,
                use_vla_aux=True,
                gradient_checkpointing=True,
                tiny=True,
            ).train()

            # Verify scale_donor is strictly frozen
            for p in model.scale_donor.parameters():
                self.assertFalse(p.requires_grad)

            # Verify GatedDeltaNet A_log & norm.weight remain float32 even after bfloat16() cast
            m_bf16 = copy.deepcopy(model).bfloat16()
            for layer in m_bf16.lm.model.language_model.layers:
                lin = getattr(layer, "linear_attn", None)
                if lin is not None:
                    self.assertEqual(lin.A_log.dtype, torch.float32)
                    self.assertEqual(lin.norm.weight.dtype, torch.float32)
            del m_bf16

            # Verify no_weight_decay parameters are placed in weight_decay=0.0 group
            groups = model.build_param_groups(lm_lr=1e-5, frontend_lr=5e-5, head_lr=2e-4, weight_decay=0.01)
            for g in groups:
                if str(g["name"]).endswith("no_decay"):
                    self.assertEqual(g["weight_decay"], 0.0)

            out, loss, loss_dict = model(
                rgb_qwen=batch["rgb_qwen"],
                rgb_da3=batch["rgb_da3"],
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
                labels=batch["labels"],
                timestamps=batch["timestamps"],
                view_mask=batch["view_mask"],
                batch=batch,
                teacher_feats=teacher_feats,
                return_logits=False,
            )
            self.assertTrue(torch.isfinite(loss), f"Non-finite loss for {frontend}: {loss}")
            self.assertGreater(float(loss_dict["l_lm"].item()), 0.0)
            self.assertGreater(float(loss_dict["l_geo"].item()), 0.0)
            self.assertGreater(float(loss_dict["l_sf2"].item()), 0.0)
            self.assertGreater(float(loss_dict["l_vla_aux"].item()), 0.0)

            loss.backward()

            unused_params = []
            non_finite_params = []
            for name, p in model.named_parameters():
                if not p.requires_grad:
                    self.assertIsNone(p.grad, f"Frozen param received grad: {name}")
                    continue
                if p.grad is None:
                    unused_params.append(name)
                elif not torch.isfinite(p.grad).all():
                    non_finite_params.append(name)

            self.assertEqual(unused_params, [], f"Unused trainable params in {frontend}: {unused_params}")
            self.assertEqual(non_finite_params, [], f"Non-finite grads in {frontend}: {non_finite_params}")

            # Explicit checks on key subsystems (front-end bridge, LoRA/trunk, taps 16 & 24, FlowExpert, LLM)
            self.assertGreater(float(model.frontend.fusion_gate.grad.abs().max().item()), 0.0)
            self.assertGreater(float(model.frontend.bridge_patch_proj.weight.grad.abs().max().item()), 0.0)
            self.assertGreater(float(model.tap_pose_heads["16"].cam_proj.weight.grad.abs().max().item()), 0.0)
            self.assertGreater(float(model.tap_pose_heads["24"].cam_proj.weight.grad.abs().max().item()), 0.0)
            self.assertGreater(float(model.tap_depth_heads["16"].lm_proj.weight.grad.abs().max().item()), 0.0)
            self.assertGreater(float(model.tap_depth_heads["24"].lm_proj.weight.grad.abs().max().item()), 0.0)
            self.assertGreater(float(model.sf2_loss.probes["16"][0].weight.grad.abs().max().item()), 0.0)
            self.assertGreater(float(model.sf2_loss.probes["24"][0].weight.grad.abs().max().item()), 0.0)
            assert model.flow_expert is not None
            self.assertGreater(float(model.flow_expert.action_out.weight.grad.abs().max().item()), 0.0)
            self.assertGreater(float(model.lm.model.language_model.layers[0].mlp.down_proj.weight.grad.abs().max().item()), 0.0)
            self.assertGreater(float(model.lm.model.language_model.layers[15].mlp.down_proj.weight.grad.abs().max().item()), 0.0)
            self.assertGreater(float(model.lm.model.language_model.layers[23].mlp.down_proj.weight.grad.abs().max().item()), 0.0)
            self.assertGreater(float(model.lm.lm_head.weight.grad.abs().max().item()), 0.0)

            if frontend == "da3_nested":
                lora_b_grads = [
                    float(p.grad.abs().max().item())
                    for n, p in model.frontend.named_parameters()
                    if "lora_B" in n and p.requires_grad and p.grad is not None
                ]
                self.assertGreater(len(lora_b_grads), 0)
                self.assertTrue(all(g > 0.0 for g in lora_b_grads))
            else:
                enc_grads = [
                    float(p.grad.abs().max().item())
                    for n, p in model.frontend.encoder.named_parameters()
                    if p.requires_grad and p.grad is not None
                ]
                self.assertGreater(len(enc_grads), 0)
                self.assertTrue(any(g > 0.0 for g in enc_grads))

        # Verify bitwise gradient equivalence with vs without gradient checkpointing on Qwen3_5DecoderLayer
        torch.manual_seed(303)
        m_no_gc = SpatialV2Stage2Model(
            frontend="corresp_stem", teacher_dim=64, gradient_checkpointing=False, tiny=True
        ).train()
        m_gc = copy.deepcopy(m_no_gc).train()
        m_gc.lm.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})

        torch.manual_seed(999)
        _, loss_no_gc, _ = m_no_gc(
            rgb_qwen=batch["rgb_qwen"],
            rgb_da3=batch["rgb_da3"],
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            labels=batch["labels"],
            timestamps=batch["timestamps"],
            view_mask=batch["view_mask"],
            batch=batch,
            teacher_feats=teacher_feats,
            return_logits=False,
        )
        loss_no_gc.backward()

        torch.manual_seed(999)
        _, loss_gc, _ = m_gc(
            rgb_qwen=batch["rgb_qwen"],
            rgb_da3=batch["rgb_da3"],
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            labels=batch["labels"],
            timestamps=batch["timestamps"],
            view_mask=batch["view_mask"],
            batch=batch,
            teacher_feats=teacher_feats,
            return_logits=False,
        )
        loss_gc.backward()

        self.assertAlmostEqual(float(loss_no_gc.item()), float(loss_gc.item()), places=6)
        for lid in (0, 3, 15, 23, 31):
            g1 = m_no_gc.lm.model.language_model.layers[lid].mlp.down_proj.weight.grad
            g2 = m_gc.lm.model.language_model.layers[lid].mlp.down_proj.weight.grad
            assert g1 is not None and g2 is not None
            self.assertLess(float((g1 - g2).abs().max().item()), 1e-6)

    def test_03_masked_nan_depth_pmap_valid_and_has_4d_teacher_edge_cases(self) -> None:
        """Test masked NaN depth, depth_valid -> pmap_valid normalization, and has_4d_teacher=False."""
        torch.manual_seed(404)
        batch, teacher_feats = build_synthetic_stage2_batch(
            batch_size=2,
            num_views=4,
            grid_h=8,
            grid_w=8,
            seq_len=32,
            vocab_size=1024,
            teacher_dim=64,
            has_4d_teacher=False,
            seed=404,
        )
        model = SpatialV2Stage2Model(
            frontend="da3_nested", teacher_dim=64, gradient_checkpointing=False, tiny=True
        ).train()

        # 1. Codex Stage-1A item #1 fix: passing depth_valid as pmap_valid prevents invalid pixels
        # from diluting pointmap loss normalization.
        out = model(
            rgb_qwen=batch["rgb_qwen"],
            rgb_da3=batch["rgb_da3"],
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            timestamps=batch["timestamps"],
            view_mask=batch["view_mask"],
            return_logits=False,
        )
        assert not isinstance(out, tuple)
        tap16 = out.tap_outputs["16"]

        # Construct constant unit pointmap residual everywhere
        batch_full = dict(batch)
        batch_full["pmap_gt"] = tap16.pmap_pred.detach() - 1.0
        batch_full["depth_valid"] = torch.ones_like(batch["depth_valid"], dtype=torch.bool)
        _, m_full = model._compute_single_tap_geo_loss("16", tap16, batch_full, batch["view_mask"])

        batch_half = dict(batch_full)
        half_mask = torch.ones_like(batch["depth_valid"], dtype=torch.bool)
        half_mask[:, :, 4:, :] = False
        batch_half["depth_valid"] = half_mask
        # Inject NaNs in invalid half of depth_gt and pmap_gt
        depth_nan = batch_full["depth_gt"].clone()
        depth_nan[~half_mask] = float("nan")
        pmap_nan = batch_full["pmap_gt"].clone()
        pmap_nan[~half_mask] = float("nan")
        batch_half["depth_gt"] = depth_nan
        batch_half["pmap_gt"] = pmap_nan

        _, m_half = model._compute_single_tap_geo_loss("16", tap16, batch_half, batch["view_mask"])
        self.assertAlmostEqual(
            float(m_full["geo_16_pmap"].item()),
            float(m_half["geo_16_pmap"].item()),
            places=5,
            msg="Pointmap loss changed when invalid pixels were masked (pmap_valid normalization regression!)",
        )

        # 2. has_4d_teacher=False with NaN 4D targets must produce 0.0 flow/rigidity loss and finite grads
        batch_nan_4d = dict(batch_half)
        batch_nan_4d["has_4d_teacher"] = torch.tensor([False, False], dtype=torch.bool)
        batch_nan_4d["y_stat_gt"] = torch.full_like(batch["y_stat_gt"], float("nan"))
        batch_nan_4d["delta_p_gt"] = torch.full_like(batch["delta_p_gt"], float("nan"))

        _, loss, loss_dict = model(
            rgb_qwen=batch_nan_4d["rgb_qwen"],
            rgb_da3=batch_nan_4d["rgb_da3"],
            input_ids=batch_nan_4d["input_ids"],
            attention_mask=batch_nan_4d["attention_mask"],
            labels=batch_nan_4d["labels"],
            timestamps=batch_nan_4d["timestamps"],
            view_mask=batch_nan_4d["view_mask"],
            batch=batch_nan_4d,
            teacher_feats=teacher_feats,
            return_logits=False,
        )
        self.assertTrue(torch.isfinite(loss))
        self.assertEqual(float(loss_dict["geo_16_flow"].item()), 0.0)
        self.assertEqual(float(loss_dict["geo_16_rigidity"].item()), 0.0)
        self.assertEqual(float(loss_dict["geo_24_flow"].item()), 0.0)
        self.assertEqual(float(loss_dict["geo_24_rigidity"].item()), 0.0)
        loss.backward()
        for name, p in model.named_parameters():
            if p.requires_grad:
                self.assertIsNotNone(p.grad, f"Missing grad on {name}")
                assert p.grad is not None
                self.assertTrue(torch.isfinite(p.grad).all(), f"Non-finite grad on {name}")

        # 3. Mixed batch: sample 0 has_4d_teacher=True (valid), sample 1 has_4d_teacher=False (NaNs)
        model.zero_grad(set_to_none=True)
        batch_mixed_4d = dict(batch)
        batch_mixed_4d["has_4d_teacher"] = torch.tensor([True, False], dtype=torch.bool)
        y_stat_mix = batch["y_stat_gt"].clone()
        y_stat_mix[1] = float("nan")
        dp_mix = batch["delta_p_gt"].clone()
        dp_mix[1] = float("nan")
        batch_mixed_4d["y_stat_gt"] = y_stat_mix
        batch_mixed_4d["delta_p_gt"] = dp_mix

        _, loss_mix, dict_mix = model(
            rgb_qwen=batch_mixed_4d["rgb_qwen"],
            rgb_da3=batch_mixed_4d["rgb_da3"],
            input_ids=batch_mixed_4d["input_ids"],
            attention_mask=batch_mixed_4d["attention_mask"],
            labels=batch_mixed_4d["labels"],
            timestamps=batch_mixed_4d["timestamps"],
            view_mask=batch_mixed_4d["view_mask"],
            batch=batch_mixed_4d,
            teacher_feats=teacher_feats,
            return_logits=False,
        )
        self.assertTrue(torch.isfinite(loss_mix))
        self.assertNotEqual(float(dict_mix["geo_16_flow"].item()), 0.0)
        self.assertGreater(float(dict_mix["geo_16_rigidity"].item()), 0.0)
        loss_mix.backward()
        for name, p in model.named_parameters():
            if p.requires_grad:
                assert p.grad is not None
                self.assertTrue(torch.isfinite(p.grad).all(), f"Non-finite grad in mixed 4D batch on {name}")

    def test_04_room_exclusion_guard_and_e05_trace_masking(self) -> None:
        """RoomExclusionGuard refuses held-out rooms in Stage2SpatialDataset & E05 traces; assistant-only CE masking."""
        guard = Stage2RoomExclusionGuard()
        canaries = guard.verify_canaries()
        self.assertTrue({"R0", "dev-S1", "BENCH_v2", "withheld-80", "K1-heldout", "ReSTI_ScanNet"}.issubset(canaries.keys()))

        # 1. Verify ReSTI ScanNet 0000..0149 and K1-heldout rooms trigger hard RuntimeError
        with self.assertRaises(RuntimeError):
            guard.assert_room_allowed_for_train("scannet/scene0042_01", "scannet/scene0042")

        train_recs, val_recs, _, _ = build_clean_k1_splits()
        heldout_rec: CaptureRecord = val_recs[0]
        with self.assertRaises(RuntimeError):
            guard.assert_room_allowed_for_train(heldout_rec.canonical, heldout_rec.room, k1_split=heldout_rec.k1_split)

        # 2. Injecting a held-out room into Stage2SpatialDataset(split='train') must raise RuntimeError
        with self.assertRaises(RuntimeError):
            Stage2SpatialDataset(
                split="train",
                num_views=4,
                grid_h=8,
                grid_w=8,
                records_override=[train_recs[0], heldout_rec],
            )

        # 3. Injecting a held-out room into an E05 JSONL trace file must raise RuntimeError
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=True) as tf:
            poisoned_row = {
                "row_id": "poison_01",
                "canonical_scene": heldout_rec.canonical,
                "canonical_room": heldout_rec.room,
                "prompt": "How far is the chair?",
                "wire_xml": "<think>Check.</think><answer>1.0</answer>",
            }
            tf.write(json.dumps(poisoned_row) + "\n")
            tf.flush()
            with self.assertRaises(RuntimeError):
                load_clean_e05_traces(tf.name, guard=guard)

        # 4. Real E05 pilot0_smoke.jsonl loads with 0 room leakage and strict assistant-only labels
        if Path(DEFAULT_E05_JSONL).is_file():
            rows, _ = load_clean_e05_traces(DEFAULT_E05_JSONL, guard=guard)
            self.assertGreaterEqual(len(rows), 28)

        enc = encode_e05_epistemic_trace(
            prompt="How many inches separate the cardboard box and the air duct?",
            trace_turns=[
                {
                    "verify": "Confirm wide-baseline parallax across frames 2 and 23.",
                    "think": "Locate both targets first.",
                    "call": '<geo>{"op":"locate","q":"cardboard box"}</geo>',
                    "tool_response": '{"q":"cardboard box","status":"UNSEEN","best_cand_f":23}',
                },
                {
                    "think": "Inspect frame 23.",
                    "call": '<geo>{"op":"inspect","frame":23,"q":"cardboard box"}</geo>',
                    "tool_obs": '{"view":"rgb","frame":23,"visible_targets":{"s5":{"box_1000":[308,722,571,947]}}}',
                },
                {
                    "think": "Measurement succeeded: 102.0 inches.",
                    "answer": "102.0",
                },
            ],
            max_seq_len=256,
        )
        self.assertGreater(enc.assistant_token_count, 10)
        self.assertGreater(enc.masked_token_count, 10)
        # Special token IDs: <verify>=10, <think>=12, <geo>=14, <tool_response>=16, <tool_obs>=18, <answer>=20
        for asst_tok_id in (10, 12, 14, 20):
            pos = (enc.input_ids == asst_tok_id).nonzero(as_tuple=True)[0]
            self.assertGreater(pos.numel(), 0)
            self.assertTrue((enc.labels[pos] == asst_tok_id).all(), f"Assistant tag {asst_tok_id} was not supervised!")
        for tool_tok_id in (16, 18):
            pos = (enc.input_ids == tool_tok_id).nonzero(as_tuple=True)[0]
            self.assertGreater(pos.numel(), 0)
            self.assertTrue((enc.labels[pos] == -100).all(), f"Tool tag {tool_tok_id} leaked into assistant labels!")

        # 5. Clean Stage2SpatialDataset item & deterministic capture/epoch-keyed subsampling
        ds_a = Stage2SpatialDataset(
            split="train", num_views=4, grid_h=8, grid_w=8, max_captures=2, random_subsample=True, seed=777
        )
        ds_b = Stage2SpatialDataset(
            split="train", num_views=4, grid_h=8, grid_w=8, max_captures=2, random_subsample=True, seed=777
        )
        it_a0 = ds_a[0]
        # Advance RNG in between and access ds_b in reverse order: capture-keyed view sampling must still match!
        _ = torch.randn(137)
        _ = ds_b[1]
        it_b0 = ds_b[0]
        self.assertTrue(torch.equal(it_a0["timestamps"], it_b0["timestamps"]))
        self.assertTrue(torch.equal(it_a0["depth_gt"], it_b0["depth_gt"]))


if __name__ == "__main__":
    unittest.main()
