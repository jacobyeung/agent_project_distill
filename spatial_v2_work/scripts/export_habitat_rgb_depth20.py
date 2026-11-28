"""Export 20-episode Habitat R2R-CE (rand100[:20]) paired RGB + GT Metric Depth + Waypoint Click frames.

Attaches both COLOR (`512x512`, `HFOV=90 deg`, `height=1.25m`) and DEPTH (`512x512`, `HFOV=90 deg`, `height=1.25m`)
sensors in `habitat_sim 0.2.4`, steps along the episode trajectory, and records 5 evenly spaced decision frames
per episode (100 paired frames total across 20 episodes / 6 scenes, ~45 MB compressed `.npz`).
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
import numpy as np

from navrun.config import Config
from navrun.episodes import load_split
from navrun.paths import SCENES
from navrun.click import label, lead_point
from vla_where.nav import floor_plane, bearing_range, travel, focal
from vla_where.vendor import nav_text as NT

LIST_PATH = Path("/scratch/jjyeung/orch_home_distill/work_vla_prechecks/lists/rand100.json")
OUT_DIR = Path("/scratch/jjyeung/orch_home_distill/work_nav_e0_probe/out")
OUT_NPZ = OUT_DIR / "habitat_rand100_smoke20_rgb_gtdepth_100frames.npz"
OUT_META = OUT_DIR / "habitat_rand100_smoke20_rgb_gtdepth_100frames_meta.json"


class RGBDEnvironment:
    """Extends navrun.sim.Environment to capture paired RGB (uint8) + GT metric depth (float32, metres)."""

    def __init__(self, config=None, scenes=SCENES):
        import habitat_sim as hs
        self.hs, self.config, self.scenes = hs, config or Config(output_format="click", controller_version="v2", render=True), scenes
        self.scene = None
        self.simulator = None
        self.agent = None
        self.pathfinder = None

    def _load(self, scene):
        if scene == self.scene:
            return
        self.close()
        hs, c = self.hs, self.config
        cfg = hs.agent.AgentConfiguration()
        cfg.height, cfg.radius = c.agent_height, c.agent_radius

        rgb_spec = hs.CameraSensorSpec()
        rgb_spec.uuid, rgb_spec.sensor_type = "rgb", hs.SensorType.COLOR
        rgb_spec.resolution, rgb_spec.position, rgb_spec.hfov = [c.rgb_px, c.rgb_px], [0, c.height_m, 0], c.hfov_deg

        depth_spec = hs.CameraSensorSpec()
        depth_spec.uuid, depth_spec.sensor_type = "depth", hs.SensorType.DEPTH
        depth_spec.resolution, depth_spec.position, depth_spec.hfov = [c.rgb_px, c.rgb_px], [0, c.height_m, 0], c.hfov_deg

        cfg.sensor_specifications = [rgb_spec, depth_spec]
        cfg.action_space = {
            name: hs.agent.ActionSpec(kind, hs.agent.ActuationSpec(amount=amount))
            for name, kind, amount in [
                ("forward", "move_forward", 0.25),
                ("turn_left", "turn_left", 15),
                ("turn_right", "turn_right", 15),
            ]
        }
        navmesh_path = self.scenes / scene / (scene + ".navmesh")
        glb_path = self.scenes / scene / (scene + ".glb")
        sc = hs.SimulatorConfiguration()
        sc.scene_id = str(glb_path)
        sc.create_renderer, sc.enable_physics = True, False
        self.simulator = hs.Simulator(hs.Configuration(sc, [cfg]))
        self.pathfinder, self.agent = self.simulator.pathfinder, self.simulator.get_agent(0)
        if not self.pathfinder.load_nav_mesh(str(navmesh_path)):
            raise ValueError(f"Could not load navmesh {navmesh_path}")
        self.pathfinder.seed(c.seed)
        self.agent.controls.move_filter_fn = self.pathfinder.try_step
        self.scene = scene

    def reset(self, episode):
        import quaternion
        self._load(episode.scene)
        s = self.hs.AgentState()
        s.position = np.array(episode.start_position, dtype=np.float32)
        x, y, z, w = episode.start_rotation
        s.rotation = np.quaternion(w, x, y, z)
        self.agent.set_state(s)
        self.episode, self.stopped, self.steps = episode, False, 0
        return self.obs()

    @property
    def position(self):
        return self.agent.state.position.astype(float)

    @property
    def heading(self):
        import quaternion
        forward = quaternion.rotate_vectors(self.agent.state.rotation, [0, 0, -1])
        return math.atan2(-forward[0], -forward[2])

    def obs(self):
        raw = self.simulator.get_sensor_observations()
        rgb = raw["rgb"][..., :3].copy()
        depth = raw["depth"].astype(np.float32).copy()
        return rgb, depth

    def step(self, action):
        if action != "stop":
            self.agent.act(action)
        self.steps += 1
        return self.obs()

    def path(self, start, end):
        p = self.hs.ShortestPath()
        p.requested_start, p.requested_end = np.asarray(start, np.float32), np.asarray(end, np.float32)
        found = self.pathfinder.find_path(p)
        return float(p.geodesic_distance), [np.asarray(x, float) for x in p.points] if found else []

    def close(self):
        self.agent = None
        if self.simulator is not None:
            self.simulator.close()
        self.simulator, self.pathfinder, self.scene = None, None, None


def main():
    t0 = time.monotonic()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    spec = json.loads(LIST_PATH.read_text())
    target_ids = list(spec["ids"][:20])
    all_eps = load_split("val_unseen")
    ep_map = {e.episode_id: e for e in all_eps}
    episodes = [ep_map[eid] for eid in target_ids]

    cfg = Config(output_format="click", controller_version="v2", render=True)
    env = RGBDEnvironment(cfg)

    rgb_list = []
    depth_list = []
    meta_records = []

    try:
        for ep_idx, ep in enumerate(episodes):
            rgb0, depth0 = env.reset(ep)
            follower = env.hs.nav.GreedyGeodesicFollower(
                env.pathfinder,
                env.agent,
                goal_radius=0.5,
                stop_key="stop",
                forward_key="forward",
                left_key="turn_left",
                right_key="turn_right",
            )
            traj_rgbs = [rgb0]
            traj_depths = [depth0]
            traj_positions = [env.position.copy()]
            traj_headings = [float(env.heading)]

            for _ in range(120):
                try:
                    act = follower.next_action_along(np.array(ep.goal, np.float32))
                except Exception:
                    break
                if act in ("stop", None):
                    break
                r, d = env.step(act)
                traj_rgbs.append(r)
                traj_depths.append(d)
                traj_positions.append(env.position.copy())
                traj_headings.append(float(env.heading))

            # Pick 5 evenly spaced viewpoints along the trajectory
            T = len(traj_rgbs)
            sample_idxs = np.linspace(0, max(0, T - 2), 5, dtype=int).tolist()
            for k_local, s_idx in enumerate(sample_idxs):
                pos = traj_positions[s_idx]
                hdg = traj_headings[s_idx]
                dist_goal, path_pts = env.path(pos, ep.goal)
                lp = lead_point(path_pts) if path_pts else pos
                click_str, click_meta = label(pos, hdg, lp, dist_goal, 1)
                parsed = NT.parse(click_str, "click", 1)
                if parsed is not None and getattr(parsed, "kind", None) == "goal":
                    u_click, v_click = float(parsed.x), float(parsed.y)
                else:
                    u_click, v_click = 0.5, 0.72

                d_img = traj_depths[s_idx]
                H, W = d_img.shape
                px_x = min(max(int(u_click * W), 0), W - 1)
                px_y = min(max(int(v_click * H), 0), H - 1)
                # 3x3 median around click pixel for GT depth
                y0, y1 = max(0, px_y - 1), min(H, px_y + 2)
                x0, x1 = max(0, px_x - 1), min(W, px_x + 2)
                patch = d_img[y0:y1, x0:x1]
                valid_p = patch[(patch > 0.1) & (patch < 20.0)]
                d_gt_click = float(np.median(valid_p)) if valid_p.size > 0 else float(d_img[px_y, px_x])

                f_px = focal(W, cfg.hfov_deg)
                px_gt = d_gt_click * (u_click * W - W / 2.0) / f_px
                beta_gt, rng_gt = bearing_range(px_gt, d_gt_click)
                leg_gt = travel(rng_gt)

                px_fp, pz_fp = floor_plane(u_click, v_click, W, cfg.hfov_deg, cfg.height_m)
                beta_fp, rng_fp = bearing_range(px_fp, pz_fp)
                leg_fp = travel(rng_fp)

                rgb_list.append(traj_rgbs[s_idx])
                depth_list.append(d_img)
                meta_records.append({
                    "frame_global_idx": len(meta_records),
                    "ep_idx": ep_idx,
                    "episode_id": ep.episode_id,
                    "scene": ep.scene,
                    "traj_step": int(s_idx),
                    "traj_len": int(T),
                    "position": pos.tolist(),
                    "heading": hdg,
                    "dist_to_goal_m": dist_goal,
                    "click_str": click_str,
                    "u_click": u_click,
                    "v_click": v_click,
                    "d_gt_click_m": d_gt_click,
                    "rng_gt_click_m": rng_gt,
                    "leg_gt_click_m": leg_gt,
                    "pz_floor_plane_m": pz_fp,
                    "rng_floor_plane_m": rng_fp,
                    "leg_floor_plane_m": leg_fp,
                })
    finally:
        env.close()

    rgb_arr = np.stack(rgb_list, axis=0)
    depth_arr = np.stack(depth_list, axis=0)
    np.savez_compressed(OUT_NPZ, rgb=rgb_arr, depth=depth_arr)
    wall = time.monotonic() - t0
    summary = {
        "episodes": len(episodes),
        "frames": len(meta_records),
        "rgb_shape": list(rgb_arr.shape),
        "depth_shape": list(depth_arr.shape),
        "npz_path": str(OUT_NPZ),
        "npz_size_mb": round(OUT_NPZ.stat().st_size / (1024 * 1024), 2),
        "wall_seconds": round(wall, 2),
        "records": meta_records,
    }
    OUT_META.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"EXPORT_OK: {len(meta_records)} frames across {len(episodes)} eps, {summary['npz_size_mb']} MB in {wall:.2f}s")


if __name__ == "__main__":
    main()
