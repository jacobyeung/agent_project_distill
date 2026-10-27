"""Install the RGB frames a frozen preparation names into the AWS data root (host side, stdlib only, write-once).

usage: frames_install.py SPEC_JSON   (spec field "frame_plans": [{"path": ..., "sha256": ...}], each an awstrain-frame-plan-v1)
Each frame is [relative path under /data2, sha256, size, mode, source, offset]:
  exists  the file is already in the data root (size checked here; the trainer hash-checks every frame it stages);
  link    a hard link to an identical data-root file under another path (bytes hash-checked);
  tar     bytes read from a member of an AWS frame archive at a fixed offset (hash-checked before publication).
Nothing is overwritten: an existing target must already hold the expected size.
"""
import hashlib
import json
import os
import sys
from pathlib import Path


def sha_file(path):
    value = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def main(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    counts = {"exists": 0, "linked": 0, "extracted": 0, "present_before": 0}
    for pin in spec.get("frame_plans", []):
        raw = Path(pin["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == pin["sha256"], "frame plan differs from its pin"
        plan = json.loads(raw)
        assert plan["schema"] == "awstrain-frame-plan-v1"
        root = plan["data2root"]
        for rel, digest, size, mode, source, offset in plan["frames"]:
            target = root + rel
            if os.path.exists(target):
                if os.path.getsize(target) != size:
                    raise SystemExit(f"FRAME_SIZE_MISMATCH {target}")
                counts["exists" if mode == "exists" else "present_before"] += 1
                continue
            if mode == "exists":
                raise SystemExit(f"FRAME_MISSING {target}")
            os.makedirs(os.path.dirname(target), exist_ok=True)
            temporary = f"{target}.part.{os.getpid()}"
            if mode == "link":
                if sha_file(source) != digest:
                    raise SystemExit(f"FRAME_LINK_SOURCE_MISMATCH {source}")
                os.link(source, temporary)
                counts["linked"] += 1
            elif mode == "tar":
                with open(source, "rb") as stream:
                    stream.seek(offset)
                    data = stream.read(size)
                if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
                    raise SystemExit(f"FRAME_ARCHIVE_MISMATCH {source}@{offset}")
                with open(temporary, "xb") as stream:
                    stream.write(data)
                os.chmod(temporary, 0o444)
                counts["extracted"] += 1
            else:
                raise SystemExit(f"unknown mode {mode}")
            os.rename(temporary, target)
    print("FRAMES_INSTALLED " + json.dumps(counts, sort_keys=True), flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
