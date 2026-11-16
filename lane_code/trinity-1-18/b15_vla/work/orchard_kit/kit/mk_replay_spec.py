"""Match LeRobot no-noops episodes to their source LIBERO HDF5 demos and write a replay spec.

The no-noops data (OpenVLA's regeneration) replays each original demo from states[0] with no-op actions dropped and keeps
the successful ones. A LeRobot episode matches demo k when its 6-D arm actions equal demo k's actions after the same no-op
filter (OpenVLA rule: |a[:6]| < 1e-4 and gripper equal to the previous original action's gripper).
usage: mk_replay_spec.py LEROBOT_DIR HDF5_DIR SUITE_LANGS.json N_PER_TASK OUT.json"""
import glob, json, os, sys
import h5py, numpy as np, pyarrow.parquet as pq

lr, hd, langs_path, n_per, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
suite_langs = json.load(open(langs_path))  # list: benchmark task_id -> language
eps = [json.loads(l) for l in open(os.path.join(lr, "meta/episodes.jsonl"))]
info = json.load(open(os.path.join(lr, "meta/info.json")))

def lerobot_actions(i):
    t = pq.read_table(os.path.join(lr, info["data_path"].format(episode_chunk=i // info["chunks_size"], episode_index=i)), columns=["action"])
    return np.stack(t.column("action").to_numpy(zero_copy_only=False)).astype(np.float64)

def noop_filter(a):
    keep = []
    for i in range(len(a)):
        prev = a[i - 1] if i > 0 else None
        noop = np.linalg.norm(a[i, :-1]) < 1e-4 and (prev is None or a[i, -1] == prev[-1])
        if not noop:
            keep.append(i)
    return a[keep]

spec, report = {"episodes": []}, []
for f in sorted(glob.glob(os.path.join(hd, "*", "*_demo.hdf5"))):
    lang = os.path.basename(f)[: -len("_demo.hdf5")].replace("_", " ")
    task_id = suite_langs.index(lang)
    cands = sorted(e["episode_index"] for e in eps if e["tasks"][0] == lang)
    acts = {i: lerobot_actions(i) for i in cands}
    with h5py.File(f, "r") as h:
        demos = sorted(h["data"].keys(), key=lambda k: int(k.split("_")[1]))
        matched = 0
        for d in demos:
            a = noop_filter(h["data"][d]["actions"][()].astype(np.float64))
            hit = [i for i, b in acts.items() if len(b) == len(a) and np.abs(b[:, :6] - a[:, :6]).max() < 1e-5]
            if len(hit) != 1:
                report.append({"demo": d, "lang": lang, "hits": hit}); continue
            i = hit[0]; b = acts.pop(i)
            grip = sorted(set(np.round(b[:, 6], 4).tolist())), sorted(set(np.round(a[:, 6], 4).tolist()))
            spec["episodes"].append({"episode_index": i, "task_id": task_id, "lang": lang, "hdf5": os.path.basename(f), "demo": d,
                                     "length": len(b), "init_state": h["data"][d]["states"][0].tolist(), "actions": b.tolist(),
                                     "gripper_values_lerobot": grip[0], "gripper_values_hdf5": grip[1]})
            matched += 1
            if matched >= n_per:
                break
    print(lang[:60], "task", task_id, "lerobot episodes", len(cands), "matched", matched)
es = [json.loads(l)["stats"]["action"] for l in open(os.path.join(lr, "meta/episodes_stats.jsonl"))]
stats = {"min": np.min([e["min"] for e in es], 0).tolist(), "max": np.max([e["max"] for e in es], 0).tolist()}
spec["random_range"] = [stats["min"], stats["max"]]
spec["unmatched_demos_seen"] = report
json.dump(spec, open(out, "w"))
print("episodes", len(spec["episodes"]), "unmatched demos seen", len(report), "action min", np.round(stats["min"], 3).tolist(), "max", np.round(stats["max"], 3).tolist())
print("gripper lerobot", spec["episodes"][0]["gripper_values_lerobot"], "hdf5", spec["episodes"][0]["gripper_values_hdf5"])
