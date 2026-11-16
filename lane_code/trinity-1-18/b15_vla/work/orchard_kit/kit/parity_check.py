"""Train/eval parity checks for LIBERO (design record 5.8.5), two stages.
extract (train_env: pyarrow + av): for every replay-spec episode, the LeRobot state and actions of frames 0..2 and the
  decoded agent-view and wrist frame 0; and every suite's LeRobot task strings.  usage: parity_check.py extract SPEC LEROBOT_ROOT OUT.npz
compare (sim_env): sets each episode's recorded init state, waits W settle steps, and reports
  - state: max |robot_state(obs) - LeRobot state[0]| per dimension for W in {0, 10} (the eval client's state convention);
  - orientation: correlation of the live agent-view / wrist frames under the four flips with LeRobot frame 0;
  - prompts: whether every suite's benchmark task language equals a LeRobot task string (the training prompts).
  usage: parity_check.py compare OUT.npz SPEC OUT.json"""
import json, os, sys
import numpy as np

SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")


def extract(spec_path, root, out):
    import av, pyarrow.parquet as pq
    spec = json.load(open(spec_path))
    d = os.path.join(root, "libero_spatial_no_noops_1.0.0_lerobot"); info = json.load(open(os.path.join(d, "meta/info.json")))
    res = {}
    for e in spec["episodes"]:
        i = e["episode_index"]; ch = i // info["chunks_size"]
        t = pq.read_table(os.path.join(d, info["data_path"].format(episode_chunk=ch, episode_index=i)), columns=["observation.state", "action"])
        res[f"state_{i}"] = np.stack(t.column("observation.state").to_numpy(zero_copy_only=False)[:3]).astype(np.float64)
        for key, vk in (("agent", "observation.images.image"), ("wrist", "observation.images.wrist_image")):
            c = av.open(os.path.join(d, info["video_path"].format(episode_chunk=ch, video_key=vk, episode_index=i)))
            res[f"{key}_{i}"] = next(c.decode(video=0)).to_ndarray(format="rgb24"); c.close()
    langs = {}
    for su in SUITES:
        f = os.path.join(root, f"{su}_no_noops_1.0.0_lerobot/meta/tasks.jsonl")
        if os.path.exists(f):
            langs[su] = [json.loads(l)["task"] for l in open(f)]
    res["langs"] = np.array(json.dumps(langs))
    np.savez(out, **res); print("extracted", len(spec["episodes"]), "episodes;", {k: len(v) for k, v in langs.items()})


def compare(npz, spec_path, out):
    import pathlib
    from libero.libero import benchmark, get_libero_path
    from libero.libero.envs import OffScreenRenderEnv
    from vl_eval import robot_state, DUMMY
    z = np.load(npz); spec = json.load(open(spec_path))
    bd = benchmark.get_benchmark_dict(); suite = bd["libero_spatial"]()
    res = {"state": {}, "orientation": {}, "prompts": {}}
    flips = {"none": lambda x: x, "ud": lambda x: x[::-1], "lr": lambda x: x[:, ::-1], "both (eval client)": lambda x: x[::-1, ::-1]}
    env, cur = None, None
    for e in spec["episodes"]:
        i = e["episode_index"]; task = suite.get_task(e["task_id"])
        if cur != e["task_id"]:
            if env is not None: env.close()
            bddl = pathlib.Path(get_libero_path("bddl_files")) / task.problem_folder / task.bddl_file
            env = OffScreenRenderEnv(bddl_file_name=str(bddl), camera_heights=256, camera_widths=256); env.seed(0); cur = e["task_id"]
        lr_state = z[f"state_{i}"][0]
        for w in (0, 10):
            env.reset(); obs = env.set_init_state(np.asarray(e["init_state"], dtype=np.float64))
            for _ in range(w): obs, *_ = env.step(DUMMY)
            d = np.abs(robot_state(obs).astype(np.float64) - lr_state)
            res["state"].setdefault(f"wait{w}", []).append(d.tolist())
            if w == 10:
                for key, ok in (("agent", "agentview_image"), ("wrist", "robot0_eye_in_hand_image")):
                    ref = z[f"{key}_{i}"].astype(np.float64).ravel()
                    for name, f in flips.items():
                        c = float(np.corrcoef(np.ascontiguousarray(f(obs[ok])).astype(np.float64).ravel(), ref)[0, 1])
                        res["orientation"].setdefault(key, {}).setdefault(name, []).append(c)
    env.close()
    for k, v in res["state"].items():
        a = np.asarray(v); res["state"][k] = {"max_abs_per_dim": a.max(0).round(5).tolist(), "median_abs_per_dim": np.median(a, 0).round(5).tolist()}
    for key, v in res["orientation"].items():
        res["orientation"][key] = {n: round(float(np.mean(c)), 4) for n, c in v.items()}
    langs = json.loads(str(z["langs"]))
    for su, tr in langs.items():
        s = bd[su](); bench = [s.get_task(t).language for t in range(s.n_tasks)]
        res["prompts"][su] = {"benchmark_tasks": len(bench), "missing_from_training": [b for b in bench if b not in tr]}
    best = {k: max(v, key=v.get) for k, v in res["orientation"].items()}
    res["orientation_best"] = best
    res["verdict"] = {"state_wait10_max": max(res["state"]["wait10"]["max_abs_per_dim"]),
                      "orientation_matches_eval_flip": all(b == "both (eval client)" for b in best.values()),
                      "prompts_match": all(not v["missing_from_training"] for v in res["prompts"].values())}
    json.dump(res, open(out, "w"), indent=1); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"extract": extract, "compare": compare}[sys.argv[1]](*sys.argv[2:5])
