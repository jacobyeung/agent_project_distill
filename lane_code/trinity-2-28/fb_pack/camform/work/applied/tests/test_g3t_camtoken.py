"""Unit and CPU round-trip tests for the G3T camera-token connector and pose/gravity prior."""
import hashlib
import json
import math
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from headcall import gate_eval as ge, phase1
from headcall.geometry import pose_from_gravity_rt
from headcall.heads import HeadBackend
from headcall.protocol import FRAME_ORIGIN
from student_pilot.camera_head import CameraHead, CameraSupervision, canon_unit_quat
from student_pilot.camera_targets import (
    GROUPS,
    gravity_reference_rotation,
    quaternion_xyzw,
    rotation_from_xyzw,
    to_gravity_reference_frame,
)
from student_pilot.gate_eval import G3T_REFERENCE
from student_pilot.geometry_input import (
    GATED_SPATIAL_INJECTION,
    GatedCameraHeadBypass,
    GatedCameraTokenConnector,
    FeatureStore,
    SPATIAL_MLLM_GATED,
)
from student_pilot.head_api import HeadSession
from tools import hc_v3, pdg_v3
from tools.g3t_camera_sidecar_store import (
    SIDECAR_SCHEMA,
    prior_from_g3t_extri_intri,
    seal as seal_camera_sidecar,
)
from tools.migrate_camtoken_init import check_heads_init, migrate_heads_checkpoint

G3T_PREDS = "/scratch/jjyeung/g3tref_20261101/preds.json"
HELDOUT_ROWS = "/scratch/jjyeung/phase2_opus/out_fix/heldout_gate2"
TRAINING_SCENES = "/scratch/jjyeung/phase2_opus/out_fix/rung1_g/TRAINING_SCENES.json"


class G3TCamTokenTests(unittest.TestCase):
    def test_canon_unit_quat_canonicalizes_and_falls_back_on_near_zero(self):
        rng = np.random.default_rng(42)
        raw = torch.tensor(rng.normal(size=(8, 16, 4)), dtype=torch.float32)
        fallback = torch.zeros_like(raw)
        fallback[..., 3] = 1.0

        q = canon_unit_quat(raw, fallback)
        norms = torch.linalg.norm(q, dim=-1)
        self.assertTrue(torch.allclose(norms, torch.ones_like(norms), atol=1e-6))
        self.assertTrue(bool((q[..., 3] >= 0).all()))
        self.assertTrue(torch.allclose(canon_unit_quat(-raw, fallback), q, atol=1e-6))
        self.assertTrue(torch.allclose(canon_unit_quat(3.5 * raw, fallback), q, atol=1e-6))

        tiny = torch.full((2, 16, 4), 1e-9, dtype=torch.float32)
        fb = torch.tensor([0.0, 0.0, -math.sqrt(0.5), -math.sqrt(0.5)], dtype=torch.float32).expand(2, 16, 4)
        out = canon_unit_quat(tiny, fb)
        self.assertTrue(torch.isfinite(out).all())
        self.assertTrue(bool((out[..., 3] >= 0).all()))
        self.assertTrue(torch.allclose(out[..., 2], torch.full((2, 16), math.sqrt(0.5)), atol=1e-6))
        self.assertTrue(torch.allclose(out[..., 3], torch.full((2, 16), math.sqrt(0.5)), atol=1e-6))

        half_turns = torch.tensor([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [math.sqrt(0.5), -math.sqrt(0.5), 0.0, 0.0],
            [0.0, math.sqrt(0.5), -math.sqrt(0.5), 0.0],
        ], dtype=torch.float32)
        q_pos = canon_unit_quat(half_turns)
        q_neg = canon_unit_quat(-half_turns)
        self.assertTrue(torch.equal(q_pos, q_neg))
        self.assertTrue(torch.allclose(q_pos, half_turns, atol=1e-6))

    def test_zero_gates_preserve_llm_carrier_and_point_depth_fov_bit_for_bit(self):
        torch.manual_seed(7)
        conn = GatedCameraTokenConnector(64, 32)
        bypass = GatedCameraHeadBypass(64, 16)
        x = torch.randn(2, 16, 64)
        self.assertEqual(float(conn(x).abs().max().item()), 0.0)
        self.assertEqual(float(bypass(x).abs().max().item()), 0.0)

        with torch.no_grad():
            conn.alpha_cam.fill_(0.4)
            bypass.alpha_bypass.fill_(-0.7)
        conn_norms = torch.linalg.norm(conn(x), dim=-1)
        bypass_norms = torch.linalg.norm(bypass(x), dim=-1)
        self.assertTrue(bool((conn_norms <= math.sqrt(32) * abs(math.tanh(0.4)) + 1e-4).all()))
        self.assertTrue(bool((bypass_norms <= math.sqrt(16) * abs(math.tanh(-0.7)) + 1e-4).all()))

        cfg = {
            "weight": 0.1,
            "weight_gravity": 0.05,
            "weight_scale": 0.02,
            "embed_dim": 32,
            "trunk_depth": 2,
            "num_heads": 4,
            "refine_iterations": 4,
            "supervision": {"path": "/fixture/camera.npz", "sha256": "a" * 64},
            "point_depth": {
                "weight": 0.05,
                "d_proj": 16,
                "mlp_hidden": 16,
                "num_heads": 4,
                "context_depth": 1,
                "vit_layers": [1, 2, 3],
            },
        }
        torch.manual_seed(11)
        base = CameraSupervision(hidden_size=64, config=cfg, vit_dim=16)
        with torch.no_grad():
            for p in base.point_depth.fov_film.parameters():
                p.normal_(0.0, 0.25)
        prior = CameraSupervision(
            hidden_size=64,
            config={**cfg, "g3t_prior": {"enabled": True, "cam_token_dim": 64}},
            vit_dim=16,
        )
        migrated = migrate_heads_checkpoint(base.state_dict(), hidden_size=64, head_dim=32, cam_token_dim=64)
        prior.load_state_dict(migrated, strict=True)

        emb_in = torch.randn(2, 40, 64)
        positions = torch.tensor([[2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32],
                                  [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31]], dtype=torch.long)
        cam_tokens = torch.randn(2, 16, 64)
        out_base = base.embedding_hook(emb_in.clone(), positions)
        out_prior = prior.embedding_hook(emb_in.clone(), positions, g3t_cam_tokens=cam_tokens)
        self.assertTrue(torch.equal(out_base, out_prior))

        carrier_states = torch.randn(2, 16, 64)
        pose_9d = torch.randn(2, 16, 9)
        pose_9d[..., 3:7] = canon_unit_quat(pose_9d[..., 3:7])
        pose_9d[..., 7:9] = torch.rand(2, 16, 2) + 0.5
        grav_up = torch.nn.functional.normalize(torch.randn(2, 3), dim=-1)
        step_scale = torch.tensor([[0.25], [0.40]], dtype=torch.float32)

        stages_b, grav_b, scale_b, fov_b = base.predict_all(carrier_states, return_fov_raw=True)
        stages_p, grav_p, scale_p, fov_p = prior.predict_all(
            carrier_states,
            g3t_cam_tokens=cam_tokens,
            g3t_pose_9d=pose_9d,
            g3t_gravity_up=grav_up,
            g3t_step_scale=step_scale,
            return_fov_raw=True,
        )
        for sb, sp in zip(scale_b, scale_p):
            self.assertTrue(torch.equal(sb, sp))
        self.assertTrue(torch.equal(fov_b, fov_p))

        with torch.autocast("cpu", dtype=torch.bfloat16):
            emb_bf16_b = base.embedding_hook(emb_in.to(torch.bfloat16).clone(), positions)
            emb_bf16_p = prior.embedding_hook(emb_in.to(torch.bfloat16).clone(), positions, g3t_cam_tokens=cam_tokens)
            self.assertTrue(torch.equal(emb_bf16_b, emb_bf16_p))
            _, _, scale_bf16_b, fov_bf16_b = base.predict_all(carrier_states.to(torch.bfloat16), return_fov_raw=True)
            _, _, scale_bf16_p, fov_bf16_p = prior.predict_all(
                carrier_states.to(torch.bfloat16),
                g3t_cam_tokens=cam_tokens,
                g3t_pose_9d=pose_9d,
                g3t_gravity_up=grav_up,
                g3t_step_scale=step_scale,
                return_fov_raw=True,
            )
            for sb, sp in zip(scale_bf16_b, scale_bf16_p):
                self.assertTrue(torch.equal(sb, sp))
            self.assertTrue(torch.equal(fov_bf16_b, fov_bf16_p))
            vis_bf16 = torch.randn(16, 4, 4, 64, dtype=torch.bfloat16)
            vit_bf16 = [torch.randn(16, 8, 8, 16, dtype=torch.bfloat16) for _ in range(3)]
            uv_pts = torch.tensor([[[0.25, 0.75], [0.5, 0.5]]] * 16, dtype=torch.float32)
            pd_b = base.point_depth(vis_bf16, vit_bf16, fov_bf16_b[0].detach().clamp(0.1, math.pi - 0.1), uv_pts)
            pd_p = prior.point_depth(vis_bf16, vit_bf16, fov_bf16_p[0].detach().clamp(0.1, math.pi - 0.1), uv_pts)
            self.assertTrue(torch.equal(pd_b, pd_p))

        vis = torch.randn(16, 4, 4, 64)
        vit = [torch.randn(16, 8, 8, 16) for _ in range(3)]
        sess_base = HeadSession(base, carrier_states[0], vis, vit)
        sess_prior = HeadSession(
            prior,
            carrier_states[0],
            vis,
            vit,
            g3t_cam_tokens=cam_tokens[0],
            g3t_pose_9d=pose_9d[0],
            g3t_gravity_up=grav_up[0],
            g3t_step_scale=step_scale[0],
        )
        pts = np.array([[250.0, 750.0], [500.0, 500.0]], dtype=np.float32)
        for frame in (2, 16, 32):
            np.testing.assert_array_equal(sess_base.depth(frame, pts), sess_prior.depth(frame, pts))

    def test_two_step_gradient_flow_opens_residual_gates_and_trains_branches(self):
        torch.manual_seed(19)
        cfg = {
            "weight": 0.1,
            "weight_gravity": 0.05,
            "weight_scale": 0.02,
            "embed_dim": 32,
            "trunk_depth": 2,
            "num_heads": 4,
            "refine_iterations": 4,
            "supervision": {"path": "/fixture/camera.npz", "sha256": "a" * 64},
            "g3t_prior": {"enabled": True, "cam_token_dim": 64},
        }
        sup = CameraSupervision(hidden_size=64, config=cfg)
        opt = torch.optim.AdamW(sup.parameters(), lr=1e-2)

        positions = torch.arange(16, dtype=torch.long)[None]
        cam_tokens = torch.randn(1, 16, 64)
        pose_9d = torch.zeros(1, 16, 9)
        pose_9d[..., :3] = torch.randn(1, 16, 3) * 0.2
        pose_9d[..., 3:7] = canon_unit_quat(torch.randn(1, 16, 4))
        pose_9d[..., 7:9] = 1.0
        grav_up = torch.nn.functional.normalize(torch.tensor([[0.1, -0.9, 0.2]], dtype=torch.float32), dim=-1)
        step_scale = torch.tensor([[0.3]], dtype=torch.float32)

        target_pose = torch.zeros(1, 16, 9)
        target_pose[..., :3] = torch.randn(1, 16, 3) * 0.5
        target_pose[..., 3:7] = canon_unit_quat(torch.randn(1, 16, 4))
        target_pose[..., 7:9] = 1.1
        targets = {
            "aux_camera_positions": positions,
            "aux_camera_target": target_pose,
            "aux_camera_mask": torch.ones(1, 16, dtype=torch.bool),
            "aux_camera_scale": torch.tensor([0.45], dtype=torch.float32),
            "aux_gravity_target": torch.nn.functional.normalize(torch.tensor([[-0.2, -0.8, 0.3]]), dim=-1),
            "aux_gravity_mask": torch.tensor([True]),
            "aux_g3t_cam_tokens": cam_tokens,
            "aux_g3t_pose_9d": pose_9d,
            "aux_g3t_gravity_up": grav_up,
            "aux_g3t_step_scale": step_scale,
        }

        def forward_loss():
            emb = sup.embedding_hook(torch.randn(1, 20, 64), positions, g3t_cam_tokens=cam_tokens)
            hidden = emb * 1.5
            return sup.loss(hidden, targets).sum()

        opt.zero_grad()
        loss1 = forward_loss()
        loss1.backward()

        self.assertGreater(float(sup.cam_token_connector.alpha_cam.grad.abs().item()), 0.0)
        self.assertGreater(float(sup.cam_head_bypass.alpha_bypass.grad.abs().item()), 0.0)
        self.assertGreater(float(sup.head.alpha_pose.grad.abs().item()), 0.0)
        self.assertGreater(float(sup.head.alpha_grav.grad.abs().item()), 0.0)
        self.assertGreater(float(sup.head.scale_branch.fc2.weight.grad.abs().max().item()), 0.0)
        self.assertEqual(float(sup.head.pose_branch.fc2.weight.grad.abs().max().item()), 0.0)
        self.assertEqual(float(sup.head.gravity_branch.fc2.weight.grad.abs().max().item()), 0.0)
        opt.step()

        opt.zero_grad()
        loss2 = forward_loss()
        loss2.backward()
        self.assertGreater(float(sup.head.pose_branch.fc2.weight.grad.abs().max().item()), 0.0)
        self.assertGreater(float(sup.head.gravity_branch.fc2.weight.grad.abs().max().item()), 0.0)
        self.assertGreater(float(sup.cam_token_connector.mlp[0].weight.grad.abs().max().item()), 0.0)
        self.assertGreater(float(sup.cam_head_bypass.fc.weight.grad.abs().max().item()), 0.0)

    def test_sidecar_store_and_migrate_camtoken_init(self):
        from tools.g3t_patch_grid_store import ENCODER as G3T_ENCODER

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame_hashes = [hashlib.sha256(f"frame-{i}".encode()).hexdigest() for i in range(32)]
            key = hashlib.sha256("\n".join(frame_hashes).encode()).hexdigest()
            patch = np.zeros((32, 4, 4, 2048), dtype=np.float16)
            patch_path = root / f"{key}.npy"
            np.save(patch_path, patch)
            patch_sha = hashlib.sha256(patch_path.read_bytes()).hexdigest()
            manifest_row = {
                "key": key,
                "frames": frame_hashes,
                "file": patch_path.name,
                "sha256": patch_sha,
                "shape": [32, 4, 4, 2048],
                "dtype": "float16",
                "layer": 23,
                "encoder": G3T_ENCODER,
            }
            manifest_path = root / "manifest.jsonl"
            manifest_path.write_text(json.dumps(manifest_row) + "\n")
            manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            sets_path = root / "sets.jsonl"
            sets_path.write_text(json.dumps({"key": key, "frames": frame_hashes}) + "\n")

            cam_path = root / f"{key}.cam.npz"
            pose_9d = np.zeros((16, 9), dtype=np.float32)
            pose_9d[:, 6] = 1.0
            pose_9d[:, 7:9] = 1.0
            np.savez(
                cam_path,
                cam_token_l23=np.ones((32, 2048), dtype=np.float16),
                local_pose_enc=np.zeros((32, 6), dtype=np.float32),
                global_pose_enc=np.zeros((32, 5), dtype=np.float32),
                coords_1024=np.tile(np.array([0.0, 0.0, 1024.0, 1024.0], dtype=np.float32), (32, 1)),
                g3t_pose_9d=pose_9d,
                g3t_gravity_up=np.array([0.0, -1.0, 0.0], dtype=np.float32),
                g3t_step_scale=np.array([0.0], dtype=np.float32),
            )
            cam_sha = hashlib.sha256(cam_path.read_bytes()).hexdigest()
            cm_row = {
                "schema": SIDECAR_SCHEMA,
                "key": key,
                "frames": frame_hashes,
                "sidecar": cam_path.name,
                "file": cam_path.name,
                "sha256": cam_sha,
                "bytes": cam_path.stat().st_size,
                "groups": 16,
                "layer": 23,
                "feature_dim": 2048,
                "encoder": G3T_ENCODER,
                "cam_token_shape": [32, 2048],
                "cam_token_dtype": "float16",
                "pose_shape": [16, 9],
                "gravity_shape": [3],
                "step_scale": 0.0,
            }
            (root / "cm_0.jsonl").write_text(json.dumps(cm_row) + "\n")
            seal_info = seal_camera_sidecar(sets_path, root)
            self.assertEqual(seal_info["selections"], 1)
            cam_manifest_path = root / "camera_manifest.jsonl"

            geom_settings = {
                "schema": "geometry-input-v1",
                "injection": GATED_SPATIAL_INJECTION,
                "encoder": G3T_ENCODER,
                "layer": 23,
                "feature_dim": 2048,
                "frames_per_token": 2,
                "projector": SPATIAL_MLLM_GATED,
                "store": {
                    "manifest": str(manifest_path),
                    "manifest_sha256": manifest_sha,
                    "camera_manifest": str(cam_manifest_path),
                    "camera_manifest_sha256": seal_info["camera_manifest"]["sha256"],
                },
            }
            store = FeatureStore(geom_settings)
            self.assertTrue(store.has_camera_sidecar)
            side = store.camera_sidecar(frame_hashes)
            self.assertEqual(tuple(side["aux_g3t_cam_tokens"].shape), (1, 16, 4096))
            self.assertEqual(tuple(side["aux_g3t_pose_9d"].shape), (1, 16, 9))
            self.assertEqual(tuple(side["aux_g3t_gravity_up"].shape), (1, 3))
            self.assertEqual(tuple(side["aux_g3t_step_scale"].shape), (1, 1))
            self.assertEqual(float(side["aux_g3t_step_scale"].item()), 0.0)

            from student_pilot import full_ft
            from student_pilot.geometry_input import empty_camera_sidecar
            from student_pilot.orchard_eval.contracts import carrier_pin
            from student_pilot.camera_config import CARRIER_TOKEN
            from tools.migrate_camtoken_init import migrate_init

            empty = empty_camera_sidecar(cam_token_dim=16)
            self.assertLess(float(empty["aux_g3t_step_scale"].item()), 0.0)

            cfg = {"weight": 0.1, "weight_gravity": 0.05, "weight_scale": 0.02, "embed_dim": 16, "trunk_depth": 1, "num_heads": 4,
                   "supervision": {"path": "/fixture/camera.npz", "sha256": "a" * 64}}
            base_sup = CameraSupervision(hidden_size=32, config=cfg)
            src_pt = root / "base_heads.pt"
            dst_pt = root / "migrated_heads.pt"
            torch.save({"camera." + k: v for k, v in base_sup.state_dict().items()}, src_pt)
            migrated = migrate_heads_checkpoint(src_pt, hidden_size=32, head_dim=16, cam_token_dim=16, seed=17)
            torch.save(migrated, dst_pt)
            migrated_again = migrate_heads_checkpoint(dst_pt, hidden_size=32, head_dim=16, cam_token_dim=16, seed=99)
            for k in migrated:
                self.assertTrue(torch.equal(migrated[k], migrated_again[k]), k)
            self.assertTrue(check_heads_init(dst_pt, hidden_size=32, head_dim=16, cam_token_dim=16))

            prior_sup = CameraSupervision(
                hidden_size=32,
                config={**cfg, "g3t_prior": {"enabled": True, "cam_token_dim": 16}},
            )
            prior_sup.load_state_dict({k.removeprefix("camera."): v for k, v in migrated.items()}, strict=True)
            with torch.no_grad():
                prior_sup.cam_head_bypass.alpha_bypass.fill_(0.5)
            states = torch.randn(2, 16, 32)
            cam_tok_2 = torch.cat([torch.ones(1, 16, 16), empty["aux_g3t_cam_tokens"]], dim=0)
            pose_2 = torch.cat([torch.as_tensor(pose_9d)[None], empty["aux_g3t_pose_9d"]], dim=0)
            grav_2 = torch.cat([torch.tensor([[0.0, -1.0, 0.0]]), empty["aux_g3t_gravity_up"]], dim=0)
            scale_2 = torch.cat([torch.tensor([[0.0]]), empty["aux_g3t_step_scale"]], dim=0)
            stages_2, grav_s2, _ = prior_sup.predict_all(
                states, g3t_cam_tokens=cam_tok_2, g3t_pose_9d=pose_2, g3t_gravity_up=grav_2, g3t_step_scale=scale_2
            )
            raw_only, raw_grav_only, _ = prior_sup.predict_all(states)
            self.assertTrue(torch.allclose(stages_2[-1][0, :, 3:7], torch.as_tensor(pose_9d[:, 3:7]), atol=1e-6))
            self.assertTrue(torch.allclose(grav_s2[-1][0], torch.tensor([0.0, -1.0, 0.0]), atol=1e-6))
            self.assertTrue(torch.equal(stages_2[-1][1], raw_only[-1][1]))
            self.assertTrue(torch.equal(grav_s2[-1][1], raw_grav_only[-1][1]))

            from student_pilot import camera_head
            with torch.no_grad():
                prior_sup.cam_token_connector.alpha_cam.fill_(0.5)
                prior_sup.cam_token_connector.mlp[2].weight.normal_(0.0, 0.05)
            emb = torch.nn.Embedding(16, 32)
            positions = torch.tensor([[0, 1], [0, 1]], dtype=torch.long)
            input_ids = torch.full((2, 4), 7, dtype=torch.long)
            batch_hook = {
                "aux_camera_positions": positions,
                "aux_g3t_cam_tokens": cam_tok_2,
                "aux_g3t_step_scale": scale_2,
            }
            for mode in ("method", "module_hook"):
                prior_sup.zero_grad(set_to_none=True)
                if mode == "method":
                    out_emb = prior_sup.embedding_hook(
                        emb(input_ids),
                        positions,
                        g3t_cam_tokens=cam_tok_2,
                        g3t_step_scale=scale_2,
                    )
                else:
                    handle = emb.register_forward_hook(camera_head.embedding_hook(prior_sup, batch_hook, 7))
                    try:
                        out_emb = emb(input_ids)
                    finally:
                        handle.remove()
                base_c0 = prior_sup.tokens[0].detach()
                base_c1 = prior_sup.tokens[1].detach()
                self.assertFalse(torch.allclose(out_emb[0, 0], base_c0))
                self.assertFalse(torch.allclose(out_emb[0, 1], base_c1))
                self.assertTrue(torch.equal(out_emb[1, 0], base_c0))
                self.assertTrue(torch.equal(out_emb[1, 1], base_c1))
                out_emb[0].sum().backward()
                self.assertIsNotNone(prior_sup.cam_token_connector.alpha_cam.grad)
                self.assertGreater(float(prior_sup.cam_token_connector.alpha_cam.grad.abs().item()), 0.0)

            src_ms = root / "ms_src"
            src_ms.mkdir(parents=True)
            export = full_ft.save_export(
                {"model.language_model.layers.0.weight": torch.zeros(2, 2, dtype=torch.bfloat16)},
                src_ms / "full_weights",
                {"student": "qwen35", "base": {}, "base_sha256": "0" * 64},
                {"mode": "full", "train": {"llm": True, "merger": True, "vision_blocks": True}},
            )
            shutil.copy2(src_pt, src_ms / "auxiliary_heads.pt")
            heads_json = src_ms / "auxiliary_heads.json"
            heads_json.write_text(json.dumps({
                "settings": {"camera": cfg},
                "inference_required": False,
                "camera": {
                    "settings": base_sup.settings,
                    "inference_required": False,
                    "carrier": {"token": CARRIER_TOKEN, "id": 151665},
                },
            }))
            ms_files = {}
            for item in export["files"]:
                rel = f"full_weights/{item['name']}"
                ms_files[rel] = {"bytes": item["bytes"], "sha256": item["sha256"]}
            for name in (export["index"]["name"], full_ft.EXPORT_MANIFEST):
                p = src_ms / "full_weights" / name
                ms_files[f"full_weights/{name}"] = {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for rel in ("auxiliary_heads.pt", "auxiliary_heads.json"):
                p = src_ms / rel
                ms_files[rel] = {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            (src_ms / "MILESTONE.json").write_text(json.dumps({
                "schema": "full-ft-milestone-export-v1",
                "step": 20,
                "identity": {},
                "files": ms_files,
            }))
            dst_ms = root / "ms_dst"
            mig_report = migrate_init(str(src_ms), str(dst_ms), seed=17, hidden_size=32, head_dim=16, cam_token_dim=16)
            mig_heads_meta = json.loads((dst_ms / "auxiliary_heads.json").read_text())
            self.assertEqual(mig_heads_meta["camera"]["carrier"], {"token": CARRIER_TOKEN, "id": 151665})
            self.assertIs(mig_heads_meta["camera"]["inference_required"], False)
            cpin = carrier_pin(
                dst_ms,
                {
                    "camera": mig_heads_meta["camera"]["settings"],
                    "auxiliary_heads": {
                        "name": "auxiliary_heads.pt",
                        "sha256": mig_report["auxiliary_heads_pt_sha256"],
                        "manifest": mig_heads_meta,
                    },
                },
                "insert",
            )
            self.assertEqual(cpin["token_id"], 151665)

            geom_file = root / "geom.safetensors"
            geom_sha = pdg_v3.write_init(geom_file, feature_dim=2048, output_dim=32, seed=17)
            pdg_v3.check_init(geom_file, geom_sha, geom_settings, output_dim=32)

    @unittest.skipUnless(
        all(os.path.exists(p) for p in (G3T_PREDS, HELDOUT_ROWS, TRAINING_SCENES)),
        "G3T reference predictions or held-out gate rows not present on this host",
    )
    def test_cpu_roundtrip_reproduces_predicted_head_gate_numbers(self):
        preds = json.loads(Path(G3T_PREDS).read_text())
        rows = ge.load_rows(HELDOUT_ROWS)
        heldout = phase1.heldout_scenes()
        training = [tuple(s) for s in json.loads(Path(TRAINING_SCENES).read_text())["scenes"]]

        def selection_key(row):
            return hashlib.sha256("\n".join(f["sha256"] for f in row["student_input"]["frames"]).encode()).hexdigest()

        gt_d, pr_d = {}, {}
        for row in rows:
            k = selection_key(row)
            for c in row["head_calls"]:
                if c["name"] == "depth":
                    tag = (c["frame"], tuple(c["point"]))
                    gt_d.setdefault(k, {})[tag] = float(c["gt"]["depth_m"])
                    pr_d.setdefault(k, {})[tag] = preds["selections"][k]["samples"]["%d|%d|%d" % (c["frame"], *c["point"])][0]
        med_scales = {k: float(np.median(list(gt_d[k].values())) / np.median([pr_d[k][t] for t in gt_d[k]]))
                      for k in preds["selections"]}
        rng = np.random.default_rng(0)
        probe_scales = {
            k: v * float(np.exp(rng.normal(0.0, 0.062 / math.sqrt(2.0 / math.pi))))
            for k, v in med_scales.items()
        }

        head = CameraHead(dim=64, depth=1, heads=4, has_gravity=True, has_scale=True, has_g3t_prior=True)
        with torch.no_grad():
            for p in head.parameters():
                p.zero_()

        class RoundTripBackend(HeadBackend):
            def __init__(self, scales):
                self.sessions = {}
                for k, sel in preds["selections"].items():
                    w2c = np.asarray(sel["w2c"], dtype=np.float64)
                    intr = np.asarray(sel["intrinsics_518"], dtype=np.float64)
                    coords = np.asarray(sel["coords_1024"], dtype=np.float64)
                    pose_9d, grav_up, step_s = prior_from_g3t_extri_intri(w2c, intr, coords)
                    s = scales[k]
                    step_val = float(step_s.reshape(-1)[0])
                    with torch.no_grad():
                        head.scale_branch.fc2.bias.fill_(math.log(max(s * step_val, 1e-4)) / 4.0)
                        stages, grav_stages, _ = head.forward_with_extras(
                            torch.zeros(1, GROUPS, 64),
                            iterations=4,
                            g3t_pose_9d=torch.as_tensor(pose_9d, dtype=torch.float32)[None],
                            g3t_gravity_up=torch.as_tensor(grav_up, dtype=torch.float32)[None],
                            g3t_step_scale=torch.tensor([[step_val]], dtype=torch.float32),
                        )
                    raw_pose = stages[-1][0].double().numpy()
                    pred_grav = grav_stages[-1][0].double().numpy()
                    r_grav, t_grav, fov_hw = to_gravity_reference_frame(raw_pose, pred_grav)
                    r_origin = gravity_reference_rotation(pred_grav)
                    self.sessions[k] = (r_origin, r_grav, t_grav, fov_hw, s, sel)

            def begin(self, context):
                HeadBackend.begin(self, context)
                key = selection_key(context.row)
                self.r_origin, self.r_grav, self.t_grav, self.fov_hw, self.s, self.sel = self.sessions[key]

            def pose(self, frame):
                if frame == FRAME_ORIGIN:
                    return pose_from_gravity_rt(self.r_origin, np.zeros(3), None)
                g = frame // 2 - 1
                return pose_from_gravity_rt(self.r_grav[g], self.t_grav[g], self.fov_hw[g])

            def depth(self, frame, point):
                return float(self.s * self.sel["samples"]["%d|%d|%d" % (frame, point[0], point[1])][0])

        report = ge.evaluate(rows, RoundTripBackend(probe_scales), heldout, training)
        summary = report["summary"]
        self.assertAlmostEqual(summary["rotation_deg"]["median"], 2.5539, places=3)
        self.assertAlmostEqual(summary["heading_deg"]["median"], 1.4178, places=4)
        self.assertAlmostEqual(summary["pitch_deg"]["median"], 0.9311, places=4)
        self.assertAlmostEqual(summary["roll_deg"]["median"], 0.8348, places=4)
        self.assertAlmostEqual(summary["position_m"]["median"], 0.1255, places=3)
        self.assertGreaterEqual(summary["row_decision_agreement"], 0.85)
        self.assertTrue(report["passed"])


if __name__ == "__main__":
    unittest.main()
