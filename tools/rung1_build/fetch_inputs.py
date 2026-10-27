"""Stage C of the rung-1 build (trinity-3-3, Python 3.6, stdlib only). All /data* reads are streamed tar | pv copies
(stream_copy.sh: gated reader registered with the IO governor, which sets the pv rate); everything else reads the node-local copy.

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


def intact(src, path, digest):
    """A staged copy counts only if it exists and, when its pin is known, matches it (a stopped or ended stream can
    leave a partial last member)."""
    if not os.path.exists(src + path):
        return False
    return digest is None or sha(open(src + path, "rb").read()) == digest


def stage(src, paths, name):
    """paths: iterable of path or (path, sha256 or None); stages every path that is missing or fails its pin."""
    pairs = [(p, None) if isinstance(p, str) else tuple(p) for p in paths]
    todo = sorted(set(p for p, digest in pairs if not intact(src, p, digest)))
    listing = os.path.join(src, name)
    with open(listing, "w") as stream:
        stream.write("".join(p + "\n" for p in todo))
    print("staging", name, len(todo), flush=True)
    if todo:
        subprocess.check_call(["bash", COPY, listing, src, "200k",
                               "rung1_build_20261027.stageC_" + name.split(".")[0], "0.2"])


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
    rng = random.Random(20261027)
    sample = rng.sample(sorted(videos), int(os.environ.get("R1_UNIFORMITY_SHARDS", "4")))
    sample_shards = [sorted(videos[v]["shards"])[-1] for v in sample]

    def group(key):
        return key[:len("scannet__sceneNNNN")] if key.startswith("scannet__") else key

    def plan_shards(manifest):
        shards = json.loads(manifest.decode())["shards"]
        exported_groups = {group(video.replace("/", "__")) for video in videos}
        spare = sorted((not os.path.basename(e["path"]).startswith("scannetppv2__"), e["path"]) for e in shards
                       if e["path"].endswith(".part_0001.jsonl")
                       and group(os.path.basename(e["path"]).split(".part_")[0]) not in exported_groups)
        pins = {e["path"]: e["sha256"] for e in shards}
        return [path for _, path in spare], pins, len(shards)

    def snapshot_pins():
        found = {}
        for video, record in videos.items():
            if intact(src, record["visibility"]["path"], record["visibility"]["sha256"]):
                found[video] = json.loads(pinned(src, record["visibility"]).decode())["scene_snapshot"]
        return found

    # As few copy turns as possible: one list holds every pinned file known before copying (contexts, visibility, the
    # scene primitives pinned by intact local visibility files, and the bank shards when the local manifest is intact).
    first = [MANIFEST] + [(v["context"]["path"], v["context"]["sha256"]) for v in videos.values()] \
        + [(v["visibility"]["path"], v["visibility"]["sha256"]) for v in videos.values()] \
        + [(p["path"], p["sha256"]) for p in snapshot_pins().values()]
    try:
        spare, shard_pins, _ = plan_shards(open(src + MANIFEST, "rb").read())
        first += [(path, shard_pins.get(path)) for path in sample_shards + spare[:1]]
    except (OSError, ValueError):
        pass
    stage(src, first, "list_c1b.txt")
    snapshots = snapshot_pins()
    assert len(snapshots) == len(videos)
    manifest = open(src + MANIFEST, "rb").read()
    spare, shard_pins, total_shards = plan_shards(manifest)
    print("bank shards", total_shards, "spare scans in unused groups", len(spare), spare[:7], flush=True)
    stage(src, [(p["path"], p["sha256"]) for p in snapshots.values()]
          + [(path, shard_pins.get(path)) for path in sample_shards + spare[:1]], "list_c2.txt")

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
