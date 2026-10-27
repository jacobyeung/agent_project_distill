"""Stage C of the rung-1 build (trinity-3-3, Python 3.6, stdlib only). All /data* reads are streamed tar | pv copies
(stream_copy.sh, 200 kB/s, pausing on the IO meter); everything else reads the node-local copy.

For every export video it stages:
  * the bank scene context each row binds (answer_provenance.source_scene): the authoritative 32-frame student input;
  * SCENE_VISIBILITY.json (GT per-frame instance visibility) and the GT scene primitives it pins (SCENE.json: 32 camera
    poses, object boxes), used only by the A3 perception targets;
and, to prove that every bank row of a video carries that same student input, four whole bank shards; plus the first
bank shard of one scan the export does not use, for the held-out support row.

usage: fetch_inputs.py SRC_ROOT
writes SRC_ROOT/VIDEO_INPUTS.jsonl, SRC_ROOT/UNIFORMITY.json, SRC_ROOT/SUPPORT_ROW.json
"""
import hashlib
import json
import os
import random
import subprocess
import sys

BANK = "/data3/jjyeung/distill_qgen/reviewed_bank_v2"
MANIFEST = ("/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/qgen_20261021/out/questions/"
            "candidate_v4/MANIFEST.json")
COPY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stream_copy.sh")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stage(src, paths, name):
    todo = sorted(set(p for p in paths if not os.path.exists(src + p)))
    listing = os.path.join(src, name)
    with open(listing, "w") as stream:
        stream.write("".join(p + "\n" for p in todo))
    print("staging", name, len(todo), flush=True)
    if todo:
        subprocess.check_call(["bash", COPY, listing, src, "200k"])


def pinned(src, pin):
    data = open(src + pin["path"], "rb").read()
    assert sha(data) == pin["sha256"], pin["path"]
    return data


def strip(inputs):
    inputs = dict(inputs)
    inputs.pop("question")
    inputs.pop("options")
    return inputs


def index_entries(src):
    """The export's item index lines in tranche order (or a test subset named by R1_INDEX_SUBSET)."""
    subset = os.environ.get("R1_INDEX_SUBSET")
    paths = [subset] if subset else ["%s%s/tranche_%04d/INDEX.jsonl" % (src, BANK, t) for t in range(1, 8)]
    for path in paths:
        for line in open(path):
            yield json.loads(line)


def main():
    src = sys.argv[1]
    videos = {}
    for entry in index_entries(src):
        item = json.loads(pinned(src, entry).decode())
        for question in item["questions"]:
            video = question["video"]
            context = question["answer_provenance"]["source_scene"]
            record = videos.setdefault(video, {"shards": set(), "visibility": question["visibility"],
                                               "context": context})
            record["shards"].add(question["qgen"]["source_row"]["shard"]["path"])
            assert record["visibility"] == question["visibility"] and record["context"] == context, video
    print("videos", len(videos), flush=True)
    stage(src, [MANIFEST] + [v["context"]["path"] for v in videos.values()]
          + [v["visibility"]["path"] for v in videos.values()], "list_c1.txt")

    snapshots = {}
    for video, record in videos.items():
        snapshots[video] = json.loads(pinned(src, record["visibility"]).decode())["scene_snapshot"]
    rng = random.Random(20261027)
    sample = rng.sample(sorted(videos), int(os.environ.get("R1_UNIFORMITY_SHARDS", "4")))
    sample_shards = [sorted(videos[v]["shards"])[-1] for v in sample]
    manifest = pinned(src, {"path": MANIFEST, "sha256": sha(open(src + MANIFEST, "rb").read())})
    shards = [entry["path"] for entry in json.loads(manifest.decode())["shards"]]

    def group(key):
        return key[:len("scannet__sceneNNNN")] if key.startswith("scannet__") else key

    exported_groups = {group(video.replace("/", "__")) for video in videos}
    spare = sorted((not os.path.basename(path).startswith("scannetppv2__"), path) for path in shards
                   if path.endswith(".part_0001.jsonl")
                   and group(os.path.basename(path).split(".part_")[0]) not in exported_groups)
    spare = [path for _, path in spare]
    print("bank shards", len(shards), "spare scans in unused groups", len(spare), spare[:7], flush=True)
    stage(src, [p["path"] for p in snapshots.values()] + sample_shards + spare[:1], "list_c2.txt")

    out = open(src + "/VIDEO_INPUTS.jsonl.part", "w")
    inputs_by_video = {}
    for video in sorted(videos):
        record = videos[video]
        context = json.loads(pinned(src, record["context"]).decode())
        scene = json.loads(pinned(src, snapshots[video]).decode())
        visibility = json.loads(pinned(src, record["visibility"]).decode())
        assert context["dataset"] + "/" + context["scene"] == video, video
        inputs = dict(context["student_media"])  # the bank context's media; each row binds its own question/options
        assert sorted(inputs) == ["fps", "frame_indices", "frames", "timestamps", "total_num_frames"], video
        frames = [frame["sha256"] for frame in inputs["frames"]]
        assert frames == [frame["sha256"] for frame in scene["student_input"]["frames"]], video
        assert frames == [frame["native_rgb"]["sha256"] for frame in visibility["frames"]], video
        assert inputs["frame_indices"] == scene["student_input"]["frame_indices"], video
        inputs_by_video[video] = inputs
        out.write(json.dumps({"video": video, "dataset": context["dataset"], "scene": context["scene"],
                              "physical_group": context["physical_group"], "context": record["context"],
                              "student_input": inputs, "visibility": record["visibility"],
                              "scene_snapshot": snapshots[video]}, sort_keys=True) + "\n")
    out.close()
    os.rename(src + "/VIDEO_INPUTS.jsonl.part", src + "/VIDEO_INPUTS.jsonl")

    uniformity = {"shards": sample_shards, "rows": 0, "identical": 0, "different": []}
    for path in sample_shards:
        for line in open(src + path, "rb"):
            row = json.loads(line.decode())
            video = row["dataset"] + "/" + row["scene"]
            assert row["student_input"]["question"] == row["question"] and row["student_input"]["options"] == row["options"]
            uniformity["rows"] += 1
            if strip(row["student_input"]) == inputs_by_video[video]:
                uniformity["identical"] += 1
            else:
                uniformity["different"].append(row["qid"])
    with open(src + "/UNIFORMITY.json", "w") as stream:
        json.dump(uniformity, stream, indent=1, sort_keys=True)
    print("uniformity", uniformity["rows"], uniformity["identical"], len(uniformity["different"]), flush=True)
    assert uniformity["rows"] > 0 and not uniformity["different"]

    first = open(src + spare[0], "rb").readline()
    row = json.loads(first.decode())
    row["_source"] = {"shard": spare[0], "line_1based": 1, "line_sha256": sha(first.rstrip(b"\n")),
                      "manifest": MANIFEST, "manifest_sha256": sha(manifest)}
    with open(src + "/SUPPORT_ROW.json", "w") as stream:
        json.dump(row, stream, sort_keys=True)
    print("STAGE_C_DONE", flush=True)


if __name__ == "__main__":
    main()
