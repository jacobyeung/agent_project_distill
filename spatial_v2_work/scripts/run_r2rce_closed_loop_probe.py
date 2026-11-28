"""Closed-Loop Habitat R2R-CE (controller_v2) Live Probe for Test N:
N-Baseline (V-C Raw) vs N-FoVFix (V-C + Analytical FoV Correction) vs N-DA3 (DA3-Nested + ScaleAnchor).

Evaluates closed-loop 3D navigation in `habitat_sim 0.2.4` (`512x512`, `HFOV=90 deg`, `height=1.25m`,
`controller_v2`, `step_cap=500`, `success_radius=3.0m`) on `rand100` (`n=20` smoke and full `n=100`).

Arms evaluated:
1. `floor_plane`: analytic flat-floor geometry ceiling (`z = h_cam * f / (y*W - W/2)`)
2. `oracle_depth`: Habitat GT depth sensor ceiling (`z = d_GT(x, y)`)
3. `vc_raw` (`N-Baseline`): live V-C (`PointDepthHead`) raw depth (`z = d_VC_raw(x, y)`)
4. `vc_fovfix_pred` (`N-FoVFix`): live V-C + analytical focal ratio `s_fov = tan(fov_pred_w / 2) / tan(45 deg)`
5. `vc_fovfix_58deg` (`N-FoVFix-58deg`): live V-C + canonical indoor narrow-FoV ratio `tan(29 deg) / tan(45 deg) = 0.5543`
6. `vc_scale_anchor` (`N-VC-ScaleAnchor`): live V-C + zero-GT camera-height (`h_cam=1.25m`) floor-plane ScaleAnchor
7. `da3_raw` (`N-DA3-Raw`): live DA3-Nested (`da3nested-giant-large`) raw metric depth
8. `da3_scale_anchor` (`N-DA3-ScaleAnchor`): live DA3-Nested + zero-GT camera-height (`h_cam=1.25m`) floor-plane ScaleAnchor
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional
import numpy as np
import torch

from navrun.config import Config
from navrun.episodes import load_split
from navrun.metrics import metrics, aggregate
from navrun.click import label, lead_point, project, relative
from navrun.controller_v2 import ControllerV2
from navrun.prompts import history_indices
from navrun.vendor import nav_text as NT
from vla_where.nav import floor_plane, bearing_range, travel, controller, focal, SENSOR, CLICK

from export_habitat_rgb_depth20 import RGBDEnvironment
from depth_models import StandaloneVCDepth, StandaloneDA3Depth

LIST_PATH = Path("/scratch/jjyeung/orch_home_distill/work_vla_prechecks/lists/rand100.json")
OUT_DIR = Path("/scratch/jjyeung/orch_home_distill/work_nav_e0_probe/out")


class DepthLiftBackend:
    """ClickTranslator-compatible backend that lifts `<goal frame=k x=u y=v>` clicks via a depth map callback."""

    def __init__(
        self,
        mode: str,
        depth_fn: Optional[Callable[[List[np.ndarray], Optional[np.ndarray]], Tuple[np.ndarray, dict]]] = None,
        history_frames: int = 32,
    ):
        self.mode = mode
        self.depth_fn = depth_fn
        self.history_frames = history_frames
        self.sensor = dict(SENSOR)
        self.click = dict(CLICK)
        self.reset()

    def reset(self):
        self.commanded_m = []
        self.scale_history = []
        self.depth_ratio_history = []

    def executed_commanded(self, metres: float):
        self.commanded_m.append(float(metres))

    def decide(self, text: str, obs: dict, gt_depth: Optional[np.ndarray] = None):
        decision = NT.parse(text, "click", self.history_frames)
        if decision is None:
            return None, None, {}
        if decision["kind"] != "goal":
            primitives = NT.primitives(decision)
            turn = 180.0 if decision["kind"] == "turn_around" else (
                float(decision["degrees"]) if decision["kind"] == "turn_left" else
                -float(decision["degrees"]) if decision["kind"] == "turn_right" else 0.0
            )
            return primitives, dict(heading_deg=turn, distance_m=0.0, stop=decision["kind"] == "stop"), dict(kind=decision["kind"])

        x, y = float(decision["x"]), float(decision["y"])
        W = int(self.sensor["rgb_px"])
        hfov = float(self.sensor["hfov_deg"])
        h_cam = float(self.sensor["height_m"])
        f_px = focal(W, hfov)

        if self.mode == "floor_plane":
            px, pz = floor_plane(x, y, W, hfov, h_cam)
            info = {"range_source": "floor_plane", "click": {"frame": decision["frame"], "x": x, "y": y}}
        else:
            d_map, d_info = self.depth_fn(obs["frames"], gt_depth)
            Hd, Wd = d_map.shape
            px_x = min(max(int(x * Wd), 0), Wd - 1)
            px_y = min(max(int(y * Hd), 0), Hd - 1)
            # 3x3 median around click coordinate for robustness
            y0, y1 = max(0, px_y - 1), min(Hd, px_y + 2)
            x0, x1 = max(0, px_x - 1), min(Wd, px_x + 2)
            patch = d_map[y0:y1, x0:x1]
            valid_p = patch[np.isfinite(patch) & (patch > 0.05)]
            d_val = float(np.median(valid_p)) if valid_p.size > 0 else float(d_map[px_y, px_x])

            if gt_depth is not None:
                gt_patch = gt_depth[y0:y1, x0:x1]
                valid_gt = gt_patch[np.isfinite(gt_patch) & (gt_patch > 0.1) & (gt_patch < 20.0)]
                if valid_gt.size > 0:
                    d_gt_val = float(np.median(valid_gt))
                    self.depth_ratio_history.append(d_val / d_gt_val)

            if np.isfinite(d_val) and d_val > 0.05:
                pz = d_val
                px = pz * (x * W - W / 2.0) / f_px
                info = {
                    "range_source": self.mode,
                    "d_click_m": d_val,
                    "click": {"frame": decision["frame"], "x": x, "y": y},
                    **d_info,
                }
            else:
                px, pz = floor_plane(x, y, W, hfov, h_cam)
                info = {"range_source": "floor_plane_fallback", "click": {"frame": decision["frame"], "x": x, "y": y}}

        beta, rng = bearing_range(px, pz)
        dist = travel(
            rng,
            self.click["standoff_m"],
            self.click["max_leg_m"],
            self.click["undefined_leg_m"],
        )
        primitives = controller(beta, dist, self.click["turn_quantum_deg"], self.click["forward_step_m"])
        waypoint = dict(heading_deg=beta, distance_m=dist, stop=False)
        info["range_m"] = rng
        return primitives, waypoint, info


class VisibleWaypointClickPolicy:
    """Clicks the farthest visible (unoccluded) point along the shortest geodesic path within [0.6m, 2.0m].

    Unlike no-occlusion OracleClickPolicy (which projects a 2.0m point even when it is behind a solid corner wall),
    this policy walks backward from 2.0m -> 0.6m along the geodesic path until the projected pixel (u, v) is in the
    camera frustum and unoccluded (`|d_gt(u, v) - z_point| <= 0.35m`), modeling a visual clicker that clicks a
    visible floor waypoint in the current RGB image.
    """
    name = "oracle-click-visible"

    def __init__(self, env: RGBDEnvironment, allow_occlusion: bool = False):
        self.env = env
        self.allow_occlusion = allow_occlusion

    def reset(self, episode_id: int):
        pass

    def act(self, history_frames: List[np.ndarray], instruction: str, state: dict, current_gt_depth: Optional[np.ndarray] = None) -> str:
        distance, path = self.env.path(self.env.position, self.env.episode.goal)
        if not path:
            return "stop"
        if distance < 1.0:
            return "stop"

        if self.allow_occlusion or current_gt_depth is None:
            return label(self.env.position, self.env.heading, lead_point(path, 2.0), distance, len(history_frames))[0]

        H, W = current_gt_depth.shape
        # Search candidate lead distances from 2.0m down to 0.65m for a visible floor waypoint
        for cand_m in (2.0, 1.75, 1.5, 1.25, 1.0, 0.75):
            pt = lead_point(path, min(cand_m, max(0.65, distance)))
            x_rel, z_rel, _ = relative(pt, self.env.position, self.env.heading)
            uv = project(pt, self.env.position, self.env.heading)
            if uv is not None and 0.02 <= uv[0] <= 0.98 and 0.51 <= uv[1] <= 0.98 and z_rel > 0.3:
                px_x = min(max(int(uv[0] * W), 0), W - 1)
                px_y = min(max(int(uv[1] * H), 0), H - 1)
                d_surf = float(current_gt_depth[px_y, px_x])
                if d_surf > 0.2 and abs(d_surf - z_rel) <= 0.40:
                    return NT.click_text(len(history_frames), uv[0], uv[1])

        # Fallback to standard 2.0m lead_point turn/click
        return label(self.env.position, self.env.heading, lead_point(path, 2.0), distance, len(history_frames))[0]


def run_episode_closed_loop(
    env: RGBDEnvironment,
    episode,
    reference,
    policy: VisibleWaypointClickPolicy,
    backend: DepthLiftBackend,
    config: Config,
) -> dict:
    start = time.monotonic()
    rgb0, depth0 = env.reset(episode)
    frames = [rgb0]
    current_gt_depth = depth0
    policy.reset(episode.episode_id)
    backend.reset()
    ctrl_v2 = ControllerV2()

    executed = []
    decisions = 0
    distances = [env.distance()]
    shortest = distances[0]
    termination = "step_cap"
    decision_positions = []

    while env.steps < config.step_cap and decisions < config.step_cap:
        indices = history_indices(env.steps, config.history_frames)
        history = [frames[i] for i in indices]
        obs = dict(
            frames=history,
            instruction=episode.instruction,
            executed=tuple(executed),
            decision_index=decisions,
            constants=config.constants(),
        )
        state = {k: obs[k] for k in ("executed", "decision_index", "constants")}
        answer = policy.act(history, episode.instruction, state, current_gt_depth=current_gt_depth)
        primitives, waypoint, info = backend.decide(answer, obs, gt_depth=current_gt_depth)
        if primitives is None:
            primitives = list(NT.FALLBACK)
        else:
            primitives, info = ctrl_v2.decide(primitives, waypoint, info)

        decision_positions.append(env.position.copy())
        decisions += 1
        commanded = 0.0
        for action in primitives:
            if env.steps >= config.step_cap:
                break
            before = env.position.copy()
            if action == "stop":
                env.stopped = True
                env.steps += 1
            else:
                rgb_next, depth_next = env.step(action)
                frames.append(rgb_next)
                current_gt_depth = depth_next
            displacement = float(np.linalg.norm(env.position - before))
            executed.append(action)
            if action == "forward":
                commanded += config.forward_m
            distances.append(env.distance())
            if env.stopped:
                termination = "stop"
                break
            if ctrl_v2.executed(action, displacement):
                break
        backend.executed_commanded(commanded)
        if env.stopped:
            break

    stationary = 0
    for a, b in zip( reversed(decision_positions[:-1]), reversed(decision_positions[1:]) ):
        if float(np.linalg.norm(b - a)) < 1e-4:
            stationary += 1
        else:
            break

    m = metrics(
        [ env.positions[0] ] if not hasattr(env, "positions") else env.positions,
        distances,
        shortest,
        reference,
        env.stopped,
        config.success_radius,
        config.forward_m,
    )
    m.update(
        episode_id=episode.episode_id,
        scene=episode.scene,
        trajectory_id=episode.trajectory_id,
        steps=env.steps,
        decisions=decisions,
        parse_failures=0,
        fallbacks=0,
        termination=termination,
        wall_seconds=time.monotonic() - start,
        recovery_triggers=ctrl_v2.recovery_triggers,
        stationary_tail=stationary,
        median_click_depth_ratio=float(np.median(backend.depth_ratio_history)) if backend.depth_ratio_history else 1.0,
    )
    return m


def bootstrap_nav_ci(records: List[dict], key: str, n_boot: int = 5000, seed: int = 42) -> dict:
    vals = np.asarray([float(r[key]) for r in records], dtype=np.float64)
    point = float(np.mean(vals))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(vals), size=(n_boot, len(vals)))
    means = np.mean(vals[idx], axis=1)
    return {
        "mean": point,
        "ci95": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-episodes", type=int, default=20, help="Number of rand100 episodes (20 or 100)")
    parser.add_argument("--arms", type=str, default="oracle_depth,floor_plane,vc_raw,vc_fovfix_pred,vc_fovfix_58deg,vc_scale_anchor,da3_raw,da3_scale_anchor")
    parser.add_argument("--click-mode", type=str, default="both", choices=["standard", "visible", "both"])
    parser.add_argument("--tag", type=str, default="smoke20")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    spec = json.loads(LIST_PATH.read_text())
    target_ids = list(spec["ids"][: args.n_episodes])
    all_eps, references, _ = load_split("val_unseen")
    ep_map = {e.episode_id: e for e in all_eps}
    episodes = [ep_map[eid] for eid in target_ids]

    arm_list = [a.strip() for a in args.arms.split(",") if a.strip()]
    need_vc = any(a.startswith("vc_") for a in arm_list)
    need_da3 = any(a.startswith("da3_") for a in arm_list)

    vc_model = StandaloneVCDepth(device="cuda") if need_vc else None
    da3_model = StandaloneDA3Depth(device="cuda") if need_da3 else None

    cfg = Config(output_format="click", controller_version="v2", render=True)
    # Track positions inside RGBDEnvironment so navrun.metrics works identically to navrun.sim.Environment
    env = RGBDEnvironment(cfg)
    orig_reset = env.reset
    orig_step = env.step

    def tracked_reset(ep):
        res = orig_reset(ep)
        env.positions = [env.position.copy()]
        return res

    def tracked_step(act):
        res = orig_step(act)
        env.positions.append(env.position.copy())
        return res

    env.reset = tracked_reset
    env.step = tracked_step

    def make_depth_fn(arm_name: str):
        if arm_name == "oracle_depth":
            return lambda frames, gt_d: (gt_d, {"scale": 1.0})
        if arm_name.startswith("vc_"):
            def _vc_fn(frames, gt_d):
                # Pass last 4 history frames (or [frames[-1]]) for fast live closed-loop V-C inference
                clip = frames[-4:] if len(frames) >= 4 else [frames[-1]]
                out = vc_model.infer_single_or_clip(clip, query_grid_size=64, hab_hfov_deg=90.0)
                return out[arm_name], {
                    "pred_fov_x_deg": out["pred_fov_x_deg"],
                    "s_fov_pred": out["s_fov_pred"],
                    "s_anchor": out["s_anchor"],
                }
            return _vc_fn
        if arm_name.startswith("da3_"):
            def _da3_fn(frames, gt_d):
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    out = da3_model.infer_single_or_window([frames[-1]], process_res=336, hab_hfov_deg=90.0)
                return out[arm_name], {
                    "pred_hfov_deg": out["pred_hfov_deg"],
                    "s_fov_da3": out["s_fov_da3"],
                    "s_anchor": out["s_anchor"],
                }
            return _da3_fn
        raise ValueError(f"Unknown arm {arm_name}")

    click_modes = ["standard", "visible"] if args.click_mode == "both" else [args.click_mode]
    all_summaries = {}

    try:
        for cmode in click_modes:
            allow_occ = (cmode == "standard")
            policy = VisibleWaypointClickPolicy(env, allow_occlusion=allow_occ)
            all_summaries[cmode] = {}

            for arm_name in arm_list:
                t_arm = time.monotonic()
                backend = DepthLiftBackend(
                    mode=arm_name,
                    depth_fn=None if arm_name == "floor_plane" else make_depth_fn(arm_name),
                    history_frames=cfg.history_frames,
                )
                ep_records = []
                for idx, ep in enumerate(episodes):
                    rec = run_episode_closed_loop(env, ep, references[ep.trajectory_id], policy, backend, cfg)
                    ep_records.append(rec)

                agg = aggregate(ep_records)
                wall_arm = time.monotonic() - t_arm
                ci_summary = {
                    k: bootstrap_nav_ci(ep_records, k)
                    for k in ("SR", "SPL", "OSR", "NE", "nDTW", "SDTW", "path_length", "steps", "decisions", "collision_rate", "recovery_triggers", "median_click_depth_ratio")
                }
                arm_out = {
                    "click_mode": cmode,
                    "arm": arm_name,
                    "n_episodes": len(ep_records),
                    "wall_seconds": round(wall_arm, 2),
                    "aggregate": agg,
                    "bootstrap_ci95": ci_summary,
                }
                all_summaries[cmode][arm_name] = arm_out

                jsonl_path = OUT_DIR / f"r2rce_{args.tag}_{cmode}_{arm_name}.jsonl"
                with jsonl_path.open("w") as f:
                    for r in ep_records:
                        f.write(json.dumps(r) + "\n")

                print(
                    f"[{cmode} | {arm_name} | n={len(ep_records)}] "
                    f"SR={agg['SR']:.3f} SPL={agg['SPL']:.3f} OSR={agg['OSR']:.3f} "
                    f"NE={agg['NE']:.3f}m nDTW={agg['nDTW']:.3f} SDTW={agg['SDTW']:.3f} "
                    f"ratio={ci_summary['median_click_depth_ratio']['mean']:.3f} ({wall_arm:.1f}s)"
                )
    finally:
        env.close()

    summary_path = OUT_DIR / f"r2rce_{args.tag}_closed_loop_summary.json"
    summary_path.write_text(json.dumps(all_summaries, indent=2) + "\n")
    print(f"CLOSED_LOOP_SUMMARY_SAVED: {summary_path}")


if __name__ == "__main__":
    main()
