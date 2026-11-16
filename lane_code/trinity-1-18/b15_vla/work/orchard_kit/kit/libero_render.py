"""LIBERO replay renderer with ground truth (for vla_where's provider pre-check and dyn_probe).

Sets every recorded simulator state of a LIBERO HDF5 demo (data/demo_k/states, stride S), and writes one np.savez_compressed
per episode in vla_where's renders.py format (no pickles):
  instruction, agent, wrist [T,H,W,3] uint8; agent_depth, wrist_depth [T,H,W] float32 metres along the optical axis;
  agent_seg, wrist_seg [T,H,W] int32 (0 = background, robot, table and walls) + seg_names JSON {id: BDDL object name};
  K_agent, K_wrist [3,3]; T_world_agent, T_world_wrist [T,4,4] camera-to-world in OpenCV axes; proprio [T,8] (the
  training state: eef xyz, eef axis-angle, finger joints); target, place (BDDL obj_of_interest); object_centres JSON
  {name: [x, y, z]} at the first frame and object_centres_per_frame (JSON list, one dict per frame); T_eef_wrist [T,4,4] (wrist camera in the eef frame of the proprio state); frame_index [T]; image_convention.
Images, depth and segmentation are in the training data's orientation: the evaluation client's raw[::-1, ::-1]. Because a
MuJoCo render is upside down (OpenGL rows), that orientation is the true camera view mirrored left-right, so K carries
fx < 0: u = -f X / Z + W / 2, v = f Y / Z + H / 2 with (X, Y, Z) in the OpenCV camera frame. self_check verifies this
by projecting every visible object's body centre and testing that it lands on that object's segmentation mask, for
both sign conventions, and stores the hit rates in the file (projection_check).
usage: libero_render.py SUITE HDF5_FILE OUT_DIR [N_DEMOS=3] [STRIDE=4] [SIZE=256]"""
import json, math, os, pathlib, sys
import h5py, numpy as np
from libero.libero import benchmark, get_libero_path
from libero.libero.envs import OffScreenRenderEnv
from vl_eval import robot_state

suite_name, h5, out = sys.argv[1], sys.argv[2], sys.argv[3]
n_demos = int(sys.argv[4]) if len(sys.argv) > 4 else 3
stride = int(sys.argv[5]) if len(sys.argv) > 5 else 4
S = int(sys.argv[6]) if len(sys.argv) > 6 else 256
os.makedirs(out, exist_ok=True)
lang = os.path.basename(h5)[: -len("_demo.hdf5")].replace("_", " ")
suite = benchmark.get_benchmark_dict()[suite_name]()
tid = [suite.get_task(i).language for i in range(suite.n_tasks)].index(lang)
task = suite.get_task(tid)
bddl = pathlib.Path(get_libero_path("bddl_files")) / task.problem_folder / task.bddl_file
env = OffScreenRenderEnv(bddl_file_name=str(bddl), camera_heights=S, camera_widths=S)
env.seed(0); env.reset()
inner = env.env
sim, model = inner.sim, inner.sim.model
CAMS = {"agent": "agentview", "wrist": "robot0_eye_in_hand"}

names = sorted(set(getattr(inner, "objects_dict", {}).keys()) | set(getattr(inner, "fixtures_dict", {}).keys()))
seg_names = {i + 1: n for i, n in enumerate(names)}
body_obj = np.zeros(model.nbody, dtype=np.int32)
for i, n in seg_names.items():
    for b in range(model.nbody):
        bn = model.body_id2name(b) or ""
        if bn == n or bn.startswith(n + "_"):
            body_obj[b] = i
geom_obj = body_obj[model.geom_bodyid]
ooi = list(inner.parsed_problem.get("obj_of_interest", []))
target, place = (ooi + ["", ""])[0], (ooi + ["", ""])[1]


def mj_to_cv(pos, mat):
    T = np.eye(4); T[:3, :3] = np.asarray(mat).reshape(3, 3) @ np.diag([1.0, -1.0, -1.0]); T[:3, 3] = pos
    return T


def intrinsics(cam, sign):
    f = 0.5 * S / math.tan(math.radians(model.cam_fovy[model.camera_name2id(cam)]) / 2)
    return np.array([[sign * f, 0, S / 2], [0, f, S / 2], [0, 0, 1.0]])


def real_depth(d):
    ext = model.stat.extent; near, far = model.vis.map.znear * ext, model.vis.map.zfar * ext
    return (near / (1.0 - d * (1.0 - near / far))).astype(np.float32)


def flip(a):
    return np.ascontiguousarray(a[::-1, ::-1])


def body_centre(name):
    for b in range(model.nbody):
        bn = model.body_id2name(b) or ""
        if bn == name or bn == name + "_main":
            return sim.data.body_xpos[b].copy()
    return None


with h5py.File(h5, "r") as f:
    demos = sorted(f["data"].keys(), key=lambda k: int(k.split("_")[1]))[:n_demos]
    for d in demos:
        states = f["data"][d]["states"][()]
        idx = list(range(0, len(states), stride))
        rec = {k: [] for k in ("agent", "wrist", "agent_depth", "wrist_depth", "agent_seg", "wrist_seg", "T_world_agent",
                               "T_world_wrist", "proprio", "T_eef_wrist")}
        centres, hits = [], {"neg_fx": [0, 0], "pos_fx": [0, 0]}
        for t in idx:
            obs = env.set_init_state(states[t])
            sim.forward()
            for key, cam in CAMS.items():
                rgb = sim.render(width=S, height=S, camera_name=cam)
                dep = sim.render(width=S, height=S, camera_name=cam, depth=True)[1]
                seg = sim.render(width=S, height=S, camera_name=cam, segmentation=True)
                ids = np.where(seg[..., 0] == 5, geom_obj[np.clip(seg[..., 1], 0, model.ngeom - 1)], 0).astype(np.int32)
                rec[key].append(flip(rgb)); rec[f"{key}_depth"].append(flip(real_depth(dep))); rec[f"{key}_seg"].append(flip(ids))
                cid = model.camera_name2id(cam)
                rec[f"T_world_{key}"].append(mj_to_cv(sim.data.cam_xpos[cid], sim.data.cam_xmat[cid]))
            rec["proprio"].append(robot_state(obs).astype(np.float64))
            q = obs["robot0_eef_quat"]; x, y, z, w = q
            Rq = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                           [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                           [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
            Te = np.eye(4); Te[:3, :3] = Rq; Te[:3, 3] = obs["robot0_eef_pos"]
            rec["T_eef_wrist"].append(np.linalg.inv(Te) @ rec["T_world_wrist"][-1])
            c = {n: body_centre(n) for n in names}
            centres.append({n: v.tolist() for n, v in c.items() if v is not None})
            for key, cam in CAMS.items():  # projection self-check on this frame
                Tw = rec[f"T_world_{key}"][-1]; segf = rec[f"{key}_seg"][-1]
                for i, n in seg_names.items():
                    if c.get(n) is None or not (segf == i).any():
                        continue
                    pc = np.linalg.inv(Tw) @ np.append(c[n], 1.0)
                    if pc[2] <= 0:
                        continue
                    for lab, sgn in (("neg_fx", -1.0), ("pos_fx", 1.0)):
                        K = intrinsics(cam, sgn); u, v = (K @ (pc[:3] / pc[2]))[:2]
                        ui, vi = int(round(u - 0.5)), int(round(v - 0.5))
                        ok = 0 <= ui < S and 0 <= vi < S and (segf[max(vi - 3, 0):vi + 4, max(ui - 3, 0):ui + 4] == i).any()
                        hits[lab][0] += int(ok); hits[lab][1] += 1
        pc_rates = {k: (v[0] / v[1] if v[1] else None) for k, v in hits.items()}
        sign = -1.0 if (pc_rates["neg_fx"] or 0) >= (pc_rates["pos_fx"] or 0) else 1.0
        arr = {k: np.stack(v) for k, v in rec.items()}
        np.savez_compressed(os.path.join(out, f"{suite_name}_t{tid}_{d}.npz"), instruction=np.array(lang),
                            K_agent=intrinsics(CAMS["agent"], sign), K_wrist=intrinsics(CAMS["wrist"], sign),
                            seg_names=np.array(json.dumps({str(k): v for k, v in seg_names.items()})),
                            target=np.array(target), place=np.array(place), object_centres=np.array(json.dumps(centres[0])),
                            object_centres_per_frame=np.array(json.dumps(centres)),
                            frame_index=np.array(idx), image_convention=np.array("eval client raw[::-1, ::-1]; fx sign %+d" % sign),
                            projection_check=np.array(json.dumps({"hit_rate": pc_rates, "counts": hits, "chosen_fx_sign": sign})),
                            **{k: (v.astype(np.uint8) if k in ("agent", "wrist") else v) for k, v in arr.items()})
        te = arr["T_eef_wrist"]
        print(json.dumps({"episode": f"{suite_name}_t{tid}_{d}", "frames": len(idx), "target": target, "place": place,
                          "projection_hit_rate": pc_rates, "fx_sign": sign,
                          "T_eef_wrist_mean_t": te[:, :3, 3].mean(0).round(4).tolist(), "T_eef_wrist_t_std": float(te[:, :3, 3].std(0).max()),
                          "depth_range_agent": [float(arr["agent_depth"].min()), float(arr["agent_depth"].max())],
                          "seg_ids_seen": sorted(int(x) for x in np.unique(arr["agent_seg"]))}), flush=True)
env.close()
print("RENDER_DONE")
