"""Pack frames that code-aws lacks into upload archives (trinity-0-13, one process, paced reads).

usage: pack_frames.py LIST_TSV OUT_DIR [SKIP_LIST]
LIST_TSV lines: sha256 <TAB> /data2 source path [<TAB> anything]. Reads at most 0.5 MB/s and pauses while the IO meter
reads above 9 MB/s. Writes OUT_DIR/frames_NNN.tar (<= 150 MB each, members k3f8/<sha[:2]>/<sha>.png, every member
sha-verified before it is added) and OUT_DIR/frames_NNN.json (sha256 -> [offset_data, size]) plus PACKED.json.
"""
import hashlib
import io
import json
import os
import sys
import tarfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from throttle import meter_total  # noqa: E402

RATE, PAUSE, CHUNK = 500000.0, 9.0, 150 * 1000 * 1000


def main():
    listing, out = sys.argv[1], sys.argv[2]
    skip = set(open(sys.argv[3]).read().split()) if len(sys.argv) > 3 else set()
    os.makedirs(out, exist_ok=True)
    rows = []
    for line in open(listing):
        parts = line.rstrip("\n").split("\t")
        if parts[0] not in skip:
            rows.append((parts[0], parts[1]))
    number, archive, offsets, size, packed = 0, None, {}, 0, []
    start, read, checked = time.time(), 0, 0.0

    def close():
        archive.close()
        name = "frames_%03d" % number
        os.rename(os.path.join(out, name + ".tar.part"), os.path.join(out, name + ".tar"))
        data = open(os.path.join(out, name + ".tar"), "rb").read()
        with open(os.path.join(out, name + ".json"), "w") as stream:
            json.dump(offsets, stream, sort_keys=True)
        packed.append({"tar": name + ".tar", "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
                       "frames": len(offsets)})
        print("packed", packed[-1], flush=True)

    for digest, path in rows:
        if time.time() - checked > 60:
            checked = time.time()
            while (meter_total() or 0) > PAUSE:
                print("pause meter", flush=True)
                time.sleep(60)
            start, read = time.time(), 0
        data = open(path, "rb").read()
        assert hashlib.sha256(data).hexdigest() == digest, path
        read += len(data)
        ahead = read / RATE - (time.time() - start)
        if ahead > 0:
            time.sleep(ahead)
        if archive is None or size + len(data) > CHUNK:
            if archive is not None:
                close()
                number += 1
            archive = tarfile.open(os.path.join(out, "frames_%03d.tar.part" % number), "w", format=tarfile.USTAR_FORMAT)
            offsets, size = {}, 0
        info = tarfile.TarInfo("k3f8/%s/%s.png" % (digest[:2], digest))
        info.size, info.mtime, info.mode = len(data), 1793059200, 0o444
        archive.addfile(info, io.BytesIO(data))
        offsets[digest] = [archive.offset - len(data) - ((512 - len(data) % 512) % 512), len(data)]
        size += len(data) + 1024
    if archive is not None:
        close()
    with open(os.path.join(out, "PACKED.json"), "w") as stream:
        json.dump(packed, stream, indent=1)
    print("PACK_DONE", len(rows), flush=True)


if __name__ == "__main__":
    main()
