"""Unit tests for KT-6 Stage-1A data pipeline, exclusion guard, models, and evaluator.

Runs cleanly under BOTH:
  - /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -m unittest spatial_v2.tests.test_stage1a -v
  - /scratch/jjyeung/envs/p1cpu/bin/pytest spatial_v2/tests/test_stage1a.py -v
"""

from __future__ import annotations

import math
import unittest

import torch

from spatial_v2.data_k1_local import (
    LocalK1CaptureDataset,
    RoomExclusionGuard,
    build_clean_k1_splits,
    collate_k1_batch,
)
from spatial_v2.eval_stage1a import compute_clip_geometry_metrics
from spatial_v2.geo_heads import project_points, so3_exp, unproject_depth
from spatial_v2.stage1a_model import DA3GiantTeacher, Stage1ACorrespondenceModel


class TestKT6Stage1A(unittest.TestCase):
    def test_01_room_exclusion_guard_canaries_and_zero_leakage(self) -> None:
        guard = RoomExclusionGuard()
        canaries = guard.verify_canaries()
        self.assertEqual(set(canaries.keys()), {"R0", "dev-S1", "BENCH_v2", "withheld-80", "K1-heldout"})
        for name, hits in canaries.items():
            self.assertIn(name, hits)

        # Verify ScanNet rescan alias stripping catches unseen rescan suffixes
        r0_scannet = sorted(k for k in guard.blocklists["R0"] if k.startswith("scannet/scene") and "_" not in k)[0]
        self.assertTrue(guard.is_forbidden_for_train(f"{r0_scannet}_07", r0_scannet))

        # Verify actual local K1 splits
        train_recs, val_recs, _, summary = build_clean_k1_splits()
        self.assertEqual(summary["train_captures"], 233)
        self.assertEqual(summary["train_rooms"], 214)
        self.assertEqual(summary["val_captures"], 53)
        self.assertEqual(summary["val_rooms"], 50)
        self.assertEqual(summary["room_overlap"], 0)
        guard.assert_clean_split(train_recs, val_recs)

        # Mutating train to inject a val room must fail hard
        with self.assertRaises(RuntimeError):
            guard.assert_clean_split(train_recs + [val_recs[0]], val_recs)

    def test_02_local_k1_dataset_geometry_and_roundtrip(self) -> None:
        ds = LocalK1CaptureDataset(split="train", num_views=4, grid_h=8, grid_w=8, max_captures=2)
        self.assertEqual(len(ds), 2)
        item = ds[0]

        self.assertEqual(tuple(item["rgb_qwen"].shape), (4, 3, 128, 128))
        self.assertEqual(tuple(item["rgb_da3"].shape), (4, 3, 112, 112))
        self.assertEqual(tuple(item["depth_gt"].shape), (4, 8, 8))
        self.assertEqual(tuple(item["plucker_gt"].shape), (4, 4, 4, 6))
        self.assertEqual(tuple(item["pmap_gt"].shape), (4, 8, 8, 3))
        self.assertEqual(float(item["metric_scale_locked"].item()), 1.0)
        self.assertTrue(torch.isfinite(item["depth_gt"]).all())
        self.assertTrue(torch.isfinite(item["rot_gt"]).all())
        self.assertTrue(torch.isfinite(item["plucker_gt"]).all())
        self.assertTrue(torch.isfinite(item["pmap_gt"]).all())

        # Canonical gravity unit norm & exact unproject <-> project roundtrip on real K1 GT
        g_norm = item["gravity_gt"].norm(dim=-1)
        self.assertTrue(torch.allclose(g_norm, torch.ones_like(g_norm), atol=1e-4))
        # View 0 camera center must sit at [0, 0, 0] after gravity leveling
        c0 = -(item["rot_gt"][0].T @ item["trans_gt"][0])
        self.assertLess(float(c0.norm().item()), 1e-4)

        pts = unproject_depth(item["depth_gt"], item["K_fine"], item["rot_gt"], item["trans_gt"])
        u, v, z = project_points(pts, item["K_fine"], item["rot_gt"], item["trans_gt"])
        valid = item["depth_valid"]
        self.assertTrue(valid.any())
        self.assertLess(float((z[valid] - item["depth_gt"][valid]).abs().max().item()), 1e-3)

    def test_03_stage1a_isolation_and_zero_unused_grads_both_arms(self) -> None:
        ds = LocalK1CaptureDataset(split="train", num_views=4, grid_h=8, grid_w=8, max_captures=2)
        batch = collate_k1_batch([ds[0], ds[1]])
        teacher = DA3GiantTeacher(ckpt_path=None, tiny=True, tiny_dim=64)
        with torch.no_grad():
            tea = teacher(batch["rgb_da3"])
        self.assertEqual(tuple(tea.shape), (2, 4, 16, 64))

        for arm in ("epi_vit", "corresp_stem"):
            model = Stage1ACorrespondenceModel(
                arm=arm, teacher_dim=64, qwen_ckpt=None, da3_ckpt=None, gradient_checkpointing=False, tiny=True
            )
            # Hard Codex Astra isolation invariants
            self.assertFalse(model.use_metric_3d_rope)
            self.assertFalse(model.use_delta_geo_bias)
            self.assertFalse(model.cfg.use_delta_geo_bias)
            # Stage-2 LM residual projections stay frozen at exact 0.0
            for proj in (model.epi_adapter.out_patch_proj, model.epi_adapter.out_cam_proj):
                self.assertFalse(proj.weight.requires_grad)
                self.assertEqual(float(proj.weight.abs().max().item()), 0.0)
                self.assertEqual(float(proj.bias.abs().max().item()), 0.0)

            # Scale parameters must be in weight_decay=0.0 group
            groups = model.build_param_groups(backbone_lr=1e-5, head_lr=1e-4, weight_decay=0.01)
            no_wd_ids = {id(p) for p in model.depth_head.no_weight_decay_parameters()}
            for g in groups:
                for p in g["params"]:
                    if id(p) in no_wd_ids:
                        self.assertEqual(g["weight_decay"], 0.0)

            # Forward + backward inside unified forward (DDP-compatible)
            rgb = batch[model.rgb_key()]
            out, loss, loss_dict = model(
                rgb,
                timestamps=batch["timestamps"],
                view_mask=batch["view_mask"],
                batch=batch,
                teacher_feats=tea,
            )
            self.assertTrue(torch.isfinite(loss))
            loss.backward()

            # Every trainable parameter must receive a finite gradient (guarantees clean DDP)
            unused = []
            non_finite = []
            for name, p in model.named_parameters():
                if not p.requires_grad:
                    continue
                if p.grad is None:
                    unused.append(name)
                elif not torch.isfinite(p.grad).all():
                    non_finite.append(name)
            self.assertEqual(unused, [], f"Unused trainable params in arm={arm}: {unused}")
            self.assertEqual(non_finite, [], f"Non-finite grads in arm={arm}: {non_finite}")

    def test_04_eval_metrics_exact_math(self) -> None:
        ds = LocalK1CaptureDataset(split="val", num_views=4, grid_h=8, grid_w=8, max_captures=1)
        it = ds[0]

        # 1. Exact GT prediction -> 0 error everywhere
        m_gt = compute_clip_geometry_metrics(
            rot_pred=it["rot_gt"],
            trans_pred=it["trans_gt"],
            depth_pred=it["depth_gt"],
            gravity_pred=it["gravity_gt"],
            log_fx_w_pred=it["log_fx_w_gt"],
            rot_gt=it["rot_gt"],
            trans_gt=it["trans_gt"],
            depth_gt=it["depth_gt"],
            depth_valid=it["depth_valid"],
            gravity_gt=it["gravity_gt"],
            log_fx_w_gt=it["log_fx_w_gt"],
            view_mask=it["view_mask"],
        )
        self.assertLess(m_gt["rot_med_deg"], 1e-3)
        self.assertLess(m_gt["trans_dir_med_deg"], 1e-3)
        self.assertLess(m_gt["absrel"], 1e-5)
        self.assertAlmostEqual(m_gt["delta1"], 1.0, places=5)
        self.assertAlmostEqual(m_gt["scale_ratio"], 1.0, places=5)
        self.assertLess(m_gt["gravity_err_deg"], 1e-3)

        # 2. Perturb view 1..3 by exact 30 deg around Z on view 0 only -> pairwise error for (0,j) = 30 deg
        r_pert = it["rot_gt"].clone()
        ang_rad = math.radians(30.0)
        r_delta = so3_exp(torch.tensor([0.0, 0.0, ang_rad], dtype=torch.float32))
        r_pert[0] = r_delta @ r_pert[0]
        m_p = compute_clip_geometry_metrics(
            rot_pred=r_pert,
            trans_pred=it["trans_gt"],
            depth_pred=it["depth_gt"] * 1.2,
            gravity_pred=it["gravity_gt"],
            log_fx_w_pred=it["log_fx_w_gt"],
            rot_gt=it["rot_gt"],
            trans_gt=it["trans_gt"],
            depth_gt=it["depth_gt"],
            depth_valid=it["depth_valid"],
            gravity_gt=it["gravity_gt"],
            log_fx_w_gt=it["log_fx_w_gt"],
            view_mask=it["view_mask"],
        )
        # 3 pairs involve view 0 (30 deg), 3 pairs do not (0 deg) -> mean = 15.0 deg
        self.assertAlmostEqual(m_p["rot_mean_deg"], 15.0, delta=0.1)
        self.assertAlmostEqual(m_p["absrel"], 0.2, delta=1e-4)
        self.assertLess(m_p["si_absrel"], 1e-4)
        self.assertAlmostEqual(m_p["scale_ratio"], 1.2, delta=1e-4)


if __name__ == "__main__":
    unittest.main()
