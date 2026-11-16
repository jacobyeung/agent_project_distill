"""LIBERO / LIBERO-Plus rollout client (pilot eval_pilot.py) with three additions for the closed-loop checks.

Episodes are (task_id, trial) pairs; worker w of W takes every W-th pair, and pairs already in the output file are
skipped, so a restarted worker resumes. The rollout logic follows StarVLA's eval_libero.py.
Additions:
  --policy random            uniform random actions inside the training data's per-dimension range (no server).
  --replay_spec FILE         episodes start from recorded demo initial states instead of the benchmark init states;
                             the server (vl_replay_server.py) returns that demo's recorded actions through the normal
                             client path, so action convention, gripper mapping and the success detector are exercised.
  --video_dir D --videos N   save agent-view | wrist mp4s for at most N episodes per worker; with --video_every M only
                             episodes whose global pair index is a multiple of M (the same episodes for every arm).
  --send_state 1             send the 8-D LeRobot-convention state (eef xyz, eef axis-angle, 2 finger joints) as
                             example['state'] (the kit's proprio head reads it; robot_state() is checked by state_check.py).
  --no_render                no cameras and no GL context (ControlEnv with use_camera_obs and the offscreen renderer
                             off): only for the blind policies (random, demo_replay); physics and the success test are
                             unchanged, and it runs on a CPU machine without a renderer.
  --policy demo_replay       the visually blind prior: from each evaluation init state, replay open loop the recorded
                             actions of a training-subset demo of the same task (--blind_spec, from mk_blind_spec.py).
Every finished episode is one JSON line (suite, task_id, trial = init-state index, success, steps), so episodes pair
across arms by (suite, task_id, trial).
"""
import argparse
import json
import math
import os
import pathlib
import re
import time

import numpy as np
from libero.libero import benchmark, get_libero_path
from libero.libero.envs import OffScreenRenderEnv

DUMMY = [0.0] * 6 + [-1.0]


def quat2axisangle(q):
    """robosuite.utils.transform_utils.quat2axisangle (quaternion x, y, z, w)."""
    q = np.asarray(q, dtype=np.float64)
    w = float(np.clip(q[3], -1.0, 1.0))
    den = math.sqrt(1.0 - w * w)
    if math.isclose(den, 0.0):
        return np.zeros(3)
    return q[:3] * 2.0 * math.acos(w) / den


def robot_state(obs):
    return np.concatenate([obs["robot0_eef_pos"], quat2axisangle(obs["robot0_eef_quat"]), obs["robot0_gripper_qpos"]]).astype(np.float32)
MAX_STEPS = {"libero_spatial": 220, "libero_object": 280, "libero_goal": 300, "libero_10": 520}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--suite", default="libero_spatial")
    p.add_argument("--plus_category", default="", help="LIBERO-Plus category, e.g. 'Camera Viewpoints'")
    p.add_argument("--trials", type=int, default=20)
    p.add_argument("--worker", type=int, default=0)
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=0)
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--wait_steps", type=int, default=10)
    p.add_argument("--limit_tasks", type=int, default=0, help="first N selected tasks (smoke runs)")
    p.add_argument("--task_ids", default="", help="comma list of task ids (overrides selection)")
    p.add_argument("--policy", default="server", choices=["server", "random", "demo_replay"])
    p.add_argument("--blind_spec", default="", help="mk_blind_spec.py output for --policy demo_replay")
    p.add_argument("--send_state", type=int, default=0)
    p.add_argument("--video_every", type=int, default=0)
    p.add_argument("--no_render", action="store_true")
    p.add_argument("--random_range", default="", help="json [[lo..],[hi..]] for --policy random")
    p.add_argument("--replay_spec", default="")
    p.add_argument("--video_dir", default="")
    p.add_argument("--videos", type=int, default=0)
    p.add_argument("--replay_wait", type=int, default=10, help="settle steps before a replay (OpenVLA's regeneration waits 10)")
    a = p.parse_args()
    if a.no_render:
        assert a.policy in ("random", "demo_replay") and not a.video_dir, "--no_render serves the blind policies only"

    suite = benchmark.get_benchmark_dict()[a.suite]()
    replay = json.load(open(a.replay_spec)) if a.replay_spec else None
    if replay:
        pairs = [(r["task_id"], k) for k, r in enumerate(replay["episodes"])]
        difficulty = {}
    else:
        if a.plus_category:
            mapping = json.load(open(os.path.join(os.environ["LIBERO_HOME"], "libero/libero/benchmark/task_classification.json")))
            sel = [it for it in mapping[a.suite] if it["category"] == a.plus_category]
            task_ids = [it["id"] - 1 for it in sel]
            difficulty = {it["id"] - 1: it.get("difficulty_level") for it in sel}
        else:
            task_ids, difficulty = list(range(suite.n_tasks)), {}
        if a.task_ids:
            task_ids = [int(x) for x in a.task_ids.split(",")]
        if a.limit_tasks:
            task_ids = task_ids[: a.limit_tasks]
        pairs = [(t, k) for t in task_ids for k in range(a.trials)]
    gidx = {pk: i for i, pk in enumerate(pairs)}
    pairs = pairs[a.worker :: a.workers]

    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            try:
                r = json.loads(line)
            except ValueError:  # a line cut by a failed write: that episode runs again and appends a full line
                continue
            done.add((r["task_id"], r["trial"]))
    pairs = [x for x in pairs if x not in done]
    if not pairs:
        return

    client = None
    if a.policy == "server":
        from examples.simBenchmarks.LIBERO.eval_files.model2libero_interface import ModelClient
        # image_size = the rendered size, so the client never resizes: the server resizes to the training size with the
        # same PIL call the training data loader uses (the client's own resize is BILINEAR, the loader's PIL's default)
        client = ModelClient(host=a.host, port=a.port, image_size=(256, 256))
    blind = json.load(open(a.blind_spec)) if a.blind_spec else None
    rng = np.random.default_rng(a.seed + 1000 * a.worker)
    lo, hi = (np.asarray(v, dtype=np.float64) for v in json.loads(a.random_range)) if a.random_range else (None, None)
    np.random.seed(a.seed)
    if os.path.exists(a.out) and os.path.getsize(a.out) > 0:  # end a line cut by a failed write before appending
        with open(a.out, "rb") as fh:
            fh.seek(-1, 2)
            cut = fh.read(1) != b"\n"
        if cut:
            with open(a.out, "a") as fh:
                fh.write("\n")
    out = open(a.out, "a")
    env, env_task, n_video = None, None, 0
    wait_steps = a.replay_wait if replay else a.wait_steps
    for task_id, trial in pairs:
        task = suite.get_task(task_id)
        if env_task != task_id:
            if env is not None:
                env.close()
            bddl = pathlib.Path(get_libero_path("bddl_files")) / task.problem_folder / task.bddl_file
            if a.no_render:
                from libero.libero.envs.env_wrapper import ControlEnv
                env = ControlEnv(bddl_file_name=str(bddl), use_camera_obs=False, has_offscreen_renderer=False, has_renderer=False)
            else:
                env = OffScreenRenderEnv(bddl_file_name=str(bddl), camera_heights=256, camera_widths=256)
            env.seed(a.seed)
            env_task = task_id
            init_states = suite.get_task_init_states(task_id)
        # LIBERO-Plus derives perturbed-task language from the file name ('... view 0 0 100 2 352 initstate 0')
        lang = re.sub(r" view [\d ]+initstate \d+$", "", task.language) if a.plus_category else task.language
        if client is not None:
            client.reset(task_description=lang)
        env.reset()
        if replay:
            rep = replay["episodes"][trial]
            assert rep["lang"] == lang, (rep["lang"], lang)
            obs = env.set_init_state(np.asarray(rep["init_state"], dtype=np.float64))
        else:
            obs = env.set_init_state(init_states[trial])
        want_video = a.video_dir and n_video < a.videos and (not a.video_every or gidx[(task_id, trial)] % a.video_every == 0)
        frames = [] if want_video else None
        if blind is not None:  # LIBERO-Plus task languages carry perturbation suffixes: use the longest training instruction prefix
            key = lang if lang in blind["by_lang"] else max((k for k in blind["by_lang"] if lang.startswith(k)), key=len)
            demos = blind["by_lang"][key]
            demo = demos[trial % len(demos)]
            blind_actions = np.asarray(demo["actions"], dtype=np.float64)
        t0, t, step, success = time.time(), 0, 0, False
        max_steps = MAX_STEPS[a.suite] if not replay else len_replay(replay["episodes"][trial]) + 20
        while t < max_steps + wait_steps:
            if t < wait_steps:
                obs, _, _, _ = env.step(DUMMY)
                t += 1
                continue
            if not a.no_render:
                img = np.ascontiguousarray(obs["agentview_image"][::-1, ::-1])
                wrist = np.ascontiguousarray(obs["robot0_eye_in_hand_image"][::-1, ::-1])
            if frames is not None:
                frames.append(np.concatenate([img, wrist], axis=1))
            if a.policy == "random":  # seeded per (task, trial), so the prior's episodes do not depend on the worker split
                if step == 0:
                    rng = np.random.default_rng([a.seed, task_id, trial])
                action = np.concatenate([rng.uniform(lo[:6], hi[:6]), [rng.choice([-1.0, 1.0])]])
            elif a.policy == "demo_replay":
                r = blind_actions[step] if step < len(blind_actions) else np.concatenate([np.zeros(6), blind_actions[-1, 6:]])
                action = np.concatenate([r[:6], [1.0 - 2.0 * (float(r[6]) > 0.5)]])  # LeRobot gripper 1 = open -> env -1
            else:
                example = {"image": [img, wrist], "lang": lang}
                if a.send_state:
                    example["state"] = robot_state(obs)
                if replay:
                    example["replay_episode"] = int(replay["episodes"][trial]["episode_index"])
                    example["replay_t"] = step
                raw = client.step(example=example, step=step)["raw_action"]
                grip = 1.0 - 2.0 * (float(np.asarray(raw["open_gripper"]).reshape(-1)[0]) > 0.5)
                action = np.concatenate([np.asarray(raw["world_vector"]).reshape(-1), np.asarray(raw["rotation_delta"]).reshape(-1), [grip]])
            obs, _, done_flag, _ = env.step(action.tolist())
            if done_flag:
                success = True
                break
            t += 1
            step += 1
        rec = {"suite": a.suite, "category": a.plus_category or None, "task_id": task_id, "task": task.name, "no_render": a.no_render,
               "difficulty": difficulty.get(task_id), "lang": lang, "policy": a.policy, "replay": bool(replay),
               "trial": trial, "success": success, "steps": step, "seconds": round(time.time() - t0, 1)}
        if replay:
            rec["episode_index"] = replay["episodes"][trial]["episode_index"]
        if blind is not None:
            rec["blind_demo"] = demo["episode_index"]; rec["blind_lang"] = key
        if frames is not None:
            import imageio
            os.makedirs(a.video_dir, exist_ok=True)
            vp = os.path.join(a.video_dir, f"w{a.worker}_t{task_id}_k{trial}_{'ok' if success else 'fail'}.mp4")
            imageio.mimsave(vp, frames, fps=20)
            rec["video"] = vp
            n_video += 1
        out.write(json.dumps(rec) + "\n")
        out.flush()
    if env is not None:
        env.close()


def len_replay(ep):
    return int(ep["length"])


if __name__ == "__main__":
    main()
