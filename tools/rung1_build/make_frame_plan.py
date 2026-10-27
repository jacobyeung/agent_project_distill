"""Write the awstrain-frame-plan-v1 that installs every frame the rung-1 rows name into the code-aws data root.

usage: make_frame_plan.py FRAMES_NEEDED.json AWS_FRAME_PLAN.json PACK_DIR UPLOAD_DIR OUT.json
  FRAMES_NEEDED.json   sha256 -> Trinity source path (from build_rung1.py)
  AWS_FRAME_PLAN.json  aws_lane2 FRAME_PLAN (sha256 -> archive + data offset + size on code-aws)
  PACK_DIR             frames_NNN.json offsets of this lane's uploaded archives (PACKED.json lists them)
  UPLOAD_DIR           code-aws directory holding those archives as <tar sha256>.tar
Every needed frame gets exactly one tar source; the plan fails if any frame has none.
"""
import json
import os
import sys

DATA2ROOT = "/lustre/fsw/portfolios/av/users/jyeung/ap/59845bf9/d/orch/data2root"


def main():
    needed_path, aws_path, pack_dir, upload_dir, out = sys.argv[1:6]
    needed = json.load(open(needed_path))
    aws = json.load(open(aws_path))["frames"]
    ours = {}
    for packed in json.load(open(os.path.join(pack_dir, "PACKED.json"))):
        offsets = json.load(open(os.path.join(pack_dir, packed["tar"][:-4] + ".json")))
        for digest, (offset, size) in offsets.items():
            ours[digest] = (upload_dir + "/" + packed["sha256"] + ".tar", offset, size)
    frames, missing, sources = [], [], {"aws_lane2": 0, "rung1_upload": 0}
    for digest in sorted(needed):
        rel = "/k3f8/%s/%s.png" % (digest[:2], digest)
        if digest in aws:
            entry = aws[digest]
            if "archive" in entry:
                frames.append([rel, digest, entry["size_bytes"], "tar", entry["archive"], entry["offset"]])
            else:  # a plain content-addressed file: read as one member at offset 0 (copied, never hard-linked)
                frames.append([rel, digest, entry["size_bytes"], "tar", entry["path"], 0])
            sources["aws_lane2"] += 1
        elif digest in ours:
            archive, offset, size = ours[digest]
            frames.append([rel, digest, size, "tar", archive, offset])
            sources["rung1_upload"] += 1
        else:
            missing.append(digest)
    if missing:
        raise SystemExit("frames without a code-aws source: %d, e.g. %s" % (len(missing), missing[:3]))
    with open(out, "w") as stream:
        json.dump({"schema": "awstrain-frame-plan-v1", "data2root": DATA2ROOT, "frames": frames}, stream,
                  sort_keys=True)
    print(json.dumps({"frames": len(frames), "sources": sources}))


if __name__ == "__main__":
    main()
