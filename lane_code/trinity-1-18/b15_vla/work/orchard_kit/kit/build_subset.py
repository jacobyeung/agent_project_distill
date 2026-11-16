"""Build a LeRobot subset view (symlinks) holding exactly the episodes listed in a spec file.

Usage: python build_subset.py <full_dataset_dir> <out_dir> <spec.json>
The spec carries "episodes" (episode indices); stats are later computed from the subset's parquets only.
"""
import json
import os
import sys

src, out, spec_path = sys.argv[1:4]
spec = json.load(open(spec_path))
kept = set(spec["episodes"])
os.makedirs(os.path.join(out, "meta"), exist_ok=True)

episodes = [json.loads(l) for l in open(os.path.join(src, "meta/episodes.jsonl"))]
keep = [e for e in episodes if e["episode_index"] in kept]
assert len(keep) == len(kept), (len(keep), len(kept))

info = json.load(open(os.path.join(src, "meta/info.json")))
chunk_size = info["chunks_size"]
for ep in keep:
    i = ep["episode_index"]
    rel = info["data_path"].format(episode_chunk=i // chunk_size, episode_index=i)
    os.makedirs(os.path.dirname(os.path.join(out, rel)), exist_ok=True)
    if not os.path.lexists(os.path.join(out, rel)):
        os.symlink(os.path.realpath(os.path.join(src, rel)), os.path.join(out, rel))
if not os.path.lexists(os.path.join(out, "videos")):
    os.symlink(os.path.realpath(os.path.join(src, "videos")), os.path.join(out, "videos"))

with open(os.path.join(out, "meta/episodes.jsonl"), "w") as f:
    for ep in keep:
        f.write(json.dumps(ep) + "\n")
with open(os.path.join(out, "meta/episodes_stats.jsonl"), "w") as f:
    for l in open(os.path.join(src, "meta/episodes_stats.jsonl")):
        if json.loads(l)["episode_index"] in kept:
            f.write(l)
for name in ("tasks.jsonl", "modality.json"):
    open(os.path.join(out, "meta", name), "w").write(open(os.path.join(src, "meta", name)).read())
n_video = len([v for v in info["features"].values() if v.get("dtype") == "video"])
info.update(total_episodes=len(keep), total_frames=sum(e["length"] for e in keep),
            total_videos=len(keep) * n_video, splits={"train": f"0:{len(keep)}"})
json.dump(info, open(os.path.join(out, "meta/info.json"), "w"), indent=4)
json.dump(dict(spec, source=src, frames=info["total_frames"]), open(os.path.join(out, "SUBSET.json"), "w"), indent=1)
print(out, len(keep), "episodes,", info["total_frames"], "frames")
