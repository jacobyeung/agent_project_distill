"""Training-frame episodes for vla_where's cache (scripts/cache_frames.py --episodes-dir): one npz per d5_s0 episode with
instruction (0-d str), agent and wrist [T,256,256,3] uint8 exactly as the training loader decodes them (dataset
orientation), proprio [T,8] (observation.state), frame_index [T] and episode (0-d str). Episode id (the cache key and the
where-dropout draw use it): f"libero_spatial/task{benchmark task index:02d}/ep{LeRobot episode_index:06d}"; the file stem is
the id with '/' written as '__'. usage: mk_where_frames.py LEROBOT_DIR SUBSET.json SUITE_LANGS.json OUT_DIR"""
import json, os, sys
import av, numpy as np, pyarrow.parquet as pq

d, spec_path, langs_path, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
info = json.load(open(os.path.join(d, "meta/info.json"))); spec = json.load(open(spec_path)); langs = json.load(open(langs_path))
tasks = {json.loads(l)["task_index"]: json.loads(l)["task"] for l in open(os.path.join(d, "meta/tasks.jsonl"))}


def frames(i, key):
    c = av.open(os.path.join(d, info["video_path"].format(episode_chunk=i // info["chunks_size"], video_key=key, episode_index=i)))
    x = np.stack([f.to_ndarray(format="rgb24") for f in c.decode(video=0)]); c.close()
    return x


for i in spec["episodes"]:
    t = pq.read_table(os.path.join(d, info["data_path"].format(episode_chunk=i // info["chunks_size"], episode_index=i)),
                      columns=["observation.state", "frame_index", "task_index"])
    prop = np.stack(t.column("observation.state").to_numpy(zero_copy_only=False)).astype(np.float64)
    lang = tasks[int(t.column("task_index")[0].as_py())]
    eid = f"libero_spatial/task{langs.index(lang):02d}/ep{i:06d}"
    agent, wrist = frames(i, "observation.images.image"), frames(i, "observation.images.wrist_image")
    assert len(agent) == len(wrist) == len(prop), (eid, len(agent), len(wrist), len(prop))
    np.savez_compressed(os.path.join(out, eid.replace("/", "__") + ".npz"), instruction=np.array(lang), episode=np.array(eid),
                        agent=agent, wrist=wrist, proprio=prop, frame_index=np.asarray(t.column("frame_index").to_numpy()))
    print(eid, len(prop), flush=True)
print("WHERE_FRAMES_DONE", len(spec["episodes"]))
