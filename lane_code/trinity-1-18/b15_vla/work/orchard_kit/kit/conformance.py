"""vla_schema_v2 conformance tests owned by vla_libero (VLA_SCHEMA.md section 12), plus the hand-eye fit.

  t5  (train_env)  Example 5: StarVLA's min-max normaliser on the synthetic subset, the clip, the gripper map g = 1 - 2 a6
                   (IPEC a6 = 1 must give g = -1) and the execution rule (schema v2: +1 iff g >= 0, the tie g = 0 included), through the kit's own code
                   (vl_heads_hook._prepare / postprocess / client_gripper and StarVLA's Normalizer).
  t6  (train_env)  On the d5_s0 demos, the per-axis correlation between action dims 0-2 and p_eef(t+1) - p_eef(t) is >= 0.9.
  t4  (sim_env)    Hand-eye fit from replayed demo states (T_eef_cam = inverse(T_world_eef from proprio) . T_world_cam), then
                   the GT target position projected through (hand-eye, proprio, MJCF intrinsics) into the dataset-
                   orientation wrist image must land inside the GT target mask on >= 19 of 20 states. Three image
                   conventions are scored: mirror (fx < 0, the kit's), none, and an in-plane 180-degree rotation.
usage: conformance.py t5 OUT.json | t6 LEROBOT_DIR SUBSET.json OUT.json | t4 HDF5_DIR OUT.json HAND_EYE_OUT.json"""
import json, math, os, sys
import numpy as np


def t5(out):
    import torch
    from starVLA.dataloader.gr00t_lerobot.transform.state_action import Normalizer
    import vl_heads_hook as H
    mn = np.array([-0.9375, -0.9375, -0.9375, -0.1875, -0.1875, -0.375]); mx = -mn
    norm = Normalizer("min_max", {"min": mn.tolist(), "max": mx.tolist()})
    raw = np.array([0.30, -0.15, -0.60, 0.0375, 0.0, -0.075])
    y = norm.forward(torch.tensor(raw, dtype=torch.float64)).numpy()
    want_y = np.array([0.32, -0.16, -0.64, 0.20, 0.00, -0.20])
    ex = [{"action": np.concatenate([raw, [0.0]])[None].repeat(8, 0), "lang": "x"},
          {"action": np.concatenate([raw, [1.0]])[None].repeat(8, 0), "lang": "x"}]
    g = [float(e["action"][0, 6]) for e in H._prepare(ex, training=True)]
    pred = np.array([[[1.30, -0.16, -0.64, 0.20, 0.00, -0.20, -0.83]]])
    a, gp = H.postprocess(pred)
    back = norm.inverse(torch.tensor(a[0, 0, :6], dtype=torch.float64)).numpy()
    want_back = np.array([0.9375, -0.15, -0.60, 0.0375, 0.0, -0.075])
    cmd = H.client_gripper(a[0, 0, 6])
    cmd_pos = H.client_gripper(H.postprocess(np.array([[[0, 0, 0, 0, 0, 0, 0.4]]]))[0][0, 0, 6])
    cmd_zero = H.client_gripper(H.postprocess(np.array([[[0, 0, 0, 0, 0, 0, 0.0]]]))[0][0, 0, 6])
    res = {"normalised": y.round(6).tolist(), "normalised_ok": bool(np.allclose(y, want_y, atol=1e-6)),
           "g_for_a6_0": g[0], "g_for_a6_1": g[1], "gripper_map_ok": g == [1.0, -1.0],
           "clipped_denormalised": back.round(6).tolist(), "denorm_ok": bool(np.allclose(back, want_back, atol=1e-6)),
           "command_for_g_-0.83": cmd, "command_for_g_0.4": cmd_pos, "command_for_g_0": cmd_zero,
           "execution_ok": cmd == -1.0 and cmd_pos == 1.0 and cmd_zero == 1.0}  # schema v2: close iff g >= 0 (tie g = 0 closes)
    res["T5"] = "PASS" if all(res[k] for k in ("normalised_ok", "gripper_map_ok", "denorm_ok", "execution_ok")) else "FAIL"
    json.dump(res, open(out, "w"), indent=1); print(json.dumps(res))


def t6(d, spec_path, out):
    import pyarrow.parquet as pq
    info = json.load(open(os.path.join(d, "meta/info.json"))); spec = json.load(open(spec_path))
    A, DP = [], []
    for i in spec["episodes"]:
        t = pq.read_table(os.path.join(d, info["data_path"].format(episode_chunk=i // info["chunks_size"], episode_index=i)),
                          columns=["action", "observation.state"])
        a = np.stack(t.column("action").to_numpy(zero_copy_only=False)).astype(np.float64)
        s = np.stack(t.column("observation.state").to_numpy(zero_copy_only=False)).astype(np.float64)
        A.append(a[:-1, :3]); DP.append(s[1:, :3] - s[:-1, :3])
    A, DP = np.concatenate(A), np.concatenate(DP)
    corr = [float(np.corrcoef(A[:, k], DP[:, k])[0, 1]) for k in range(3)]
    cross = [[round(float(np.corrcoef(A[:, i], DP[:, j])[0, 1]), 3) for j in range(3)] for i in range(3)]
    res = {"frames": int(len(A)), "episodes": len(spec["episodes"]), "per_axis_corr": [round(c, 4) for c in corr],
           "cross_corr_action_rows_dp_cols": cross, "T6": "PASS" if all(c >= 0.9 for c in corr) else "FAIL"}
    json.dump(res, open(out, "w"), indent=1); print(json.dumps(res))


def axisangle_to_R(v):
    th = float(np.linalg.norm(v))
    if th < 1e-12:
        return np.eye(3)
    k = v / th; Kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * Kx + (1 - math.cos(th)) * Kx @ Kx


def t4(hdf5_dir, out, he_out, n_states=20, S=256):
    import glob, hashlib, pathlib
    import h5py
    from libero.libero import benchmark, get_libero_path
    from libero.libero.envs import OffScreenRenderEnv
    from vl_eval import robot_state
    suite = benchmark.get_benchmark_dict()["libero_spatial"]()
    langs = [suite.get_task(i).language for i in range(suite.n_tasks)]
    files = sorted(glob.glob(os.path.join(hdf5_dir, "libero_spatial", "*_demo.hdf5")))
    states = []  # (file, demo, t)
    for f in files:
        with h5py.File(f, "r") as h:
            for d in sorted(h["data"].keys(), key=lambda k: int(k.split("_")[1]))[:3]:
                n = len(h["data"][d]["states"])
                states += [(f, d, t) for t in np.linspace(0, n - 1, 12).astype(int)]
    rows, fits = [], []
    env, cur = None, None
    for f, d, t in states:
        lang = os.path.basename(f)[: -len("_demo.hdf5")].replace("_", " ")
        if cur != f:
            if env is not None:
                env.close()
            task = suite.get_task(langs.index(lang))
            env = OffScreenRenderEnv(bddl_file_name=str(pathlib.Path(get_libero_path("bddl_files")) / task.problem_folder / task.bddl_file),
                                     camera_heights=S, camera_widths=S)
            env.seed(0); env.reset(); cur = f
            inner = env.env; sim, model = inner.sim, inner.sim.model
            target = inner.parsed_problem["obj_of_interest"][0]
            tb = [b for b in range(model.nbody) if (model.body_id2name(b) or "") in (target, target + "_main")][0]
            obj_bodies = [b for b in range(model.nbody) if (model.body_id2name(b) or "").startswith(target)]
            geom_is_target = np.isin(model.geom_bodyid, obj_bodies)
            cid = model.camera_name2id("robot0_eye_in_hand")
            f_px = 0.5 * S / math.tan(math.radians(model.cam_fovy[cid]) / 2)
        with h5py.File(f, "r") as h:
            st = h["data"][d]["states"][t]
        obs = env.set_init_state(st); sim.forward()
        p = robot_state(obs).astype(np.float64)
        T_we = np.eye(4); T_we[:3, :3] = axisangle_to_R(p[3:6]); T_we[:3, 3] = p[:3]
        T_wc = np.eye(4); T_wc[:3, :3] = np.asarray(sim.data.cam_xmat[cid]).reshape(3, 3) @ np.diag([1.0, -1.0, -1.0])
        T_wc[:3, 3] = sim.data.cam_xpos[cid]
        fits.append(np.linalg.inv(T_we) @ T_wc)
        seg = sim.render(width=S, height=S, camera_name="robot0_eye_in_hand", segmentation=True)
        mask = np.ascontiguousarray(((seg[..., 0] == 5) & geom_is_target[np.clip(seg[..., 1], 0, model.ngeom - 1)])[::-1, ::-1])
        rows.append({"file": os.path.basename(f), "demo": d, "t": int(t), "T_we": T_we, "mask": mask,
                     "target_world": sim.data.body_xpos[tb].copy(), "mask_px": int(mask.sum())})
    env.close()
    Ts = np.stack(fits); t_he = Ts[:, :3, 3].mean(0)
    U, _, Vt = np.linalg.svd(Ts[:, :3, :3].sum(0)); R_he = U @ Vt
    T_he = np.eye(4); T_he[:3, :3] = R_he; T_he[:3, 3] = t_he
    resid_t = float(np.abs(Ts[:, :3, 3] - t_he).max())
    resid_R = float(max(np.degrees(np.arccos(np.clip((np.trace(R_he.T @ T[:3, :3]) - 1) / 2, -1, 1))) for T in Ts))
    he = {"schema": "vla_schema_v1", "T_eef_cam": T_he.tolist(), "t_he_m": t_he.round(6).tolist(),
          "camera": "robot0_eye_in_hand", "eef_frame": "proprio: eef xyz + axis-angle (robot0_eef_pos, quat2axisangle(robot0_eef_quat))",
          "camera_axes": "OpenCV axes of the MuJoCo render (R_mujoco . diag(1, -1, -1)); the dataset-orientation image is that view mirrored left-right, so K = [[-f, 0, W/2], [0, f, H/2], [0, 0, 1]]",
          "f_px_at_256": f_px, "frames": len(Ts), "max_residual_t_m": resid_t, "max_residual_R_deg": resid_R}
    he["sha256"] = hashlib.sha256(json.dumps({k: he[k] for k in ("T_eef_cam", "camera", "eef_frame", "camera_axes")}, sort_keys=True).encode()).hexdigest()
    json.dump(he, open(he_out, "w"), indent=1)
    conv = {"mirror_fx_neg (kit)": (-1, 1), "none": (1, 1), "rot180 (schema 0 alternative)": (-1, -1)}
    vis = [r for r in rows if r["mask_px"] >= 20][:n_states]
    score = {}
    for name, (sx, sy) in conv.items():
        K = np.array([[sx * f_px, 0, S / 2], [0, sy * f_px, S / 2], [0, 0, 1.0]]); hits = 0
        for r in vis:
            pc = np.linalg.inv(r["T_we"] @ T_he) @ np.append(r["target_world"], 1.0)
            if pc[2] <= 0:
                continue
            u, v = (K @ (pc[:3] / pc[2]))[:2]
            ui, vi = int(math.floor(u)), int(math.floor(v))
            hits += int(0 <= ui < S and 0 <= vi < S and bool(r["mask"][vi, ui]))
        score[name] = hits
    res = {"states_scored": len(vis), "states_rendered": len(rows), "hits_per_convention": score, "hand_eye": he_out,
           "hand_eye_t": he["t_he_m"], "hand_eye_residual_t_m": resid_t, "hand_eye_residual_R_deg": resid_R,
           "T4": "PASS" if len(vis) >= 20 and score["mirror_fx_neg (kit)"] >= 19 else "FAIL"}
    json.dump(res, open(out, "w"), indent=1); print(json.dumps(res))


if __name__ == "__main__":
    {"t5": t5, "t6": t6, "t4": t4}[sys.argv[1]](*sys.argv[2:])
