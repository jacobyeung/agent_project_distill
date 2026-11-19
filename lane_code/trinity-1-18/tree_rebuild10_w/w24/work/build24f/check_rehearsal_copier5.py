"""One shipped-copier pass over a synthetic node-local export receipt."""
from pathlib import Path
import json, sys, tarfile
D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from rehearsal_copier5 import R, sha, put, read, make_copier
kit = Path(sys.argv[1]).resolve()
root = R / "copier_synthetic"
root.mkdir(parents=True, exist_ok=False)
export = root / "train/m2"; export.mkdir(parents=True)
(export / "weights.bin").write_bytes(b"local synthetic weights\n" * 43)
marker = export / "artifact.json"
put(marker, dict(step=2, files={"weights.bin": sha(export / "weights.bin")}))
identity = sha(marker); persist = root / "train/persist"; persist.mkdir()
archive = persist / (identity + ".tar")
with tarfile.open(archive, "w") as stream:
    for path in sorted(export.iterdir()): stream.add(path, arcname=path.name, recursive=False)
receipt = dict(source=dict(path=str(marker), sha256=identity), durable=False, parts=[],
               archive=dict(path=str(archive), sha256=sha(archive), bytes=archive.stat().st_size))
put(persist / (identity + ".local.json"), receipt)
c, evidence = make_copier(kit, root)
c.pass_once()
done = root / "target/o/rehearsal/live/gcs_m2.done"
sent = read(done)
assert sent["marker_sha256"] == identity and sent["sha256"] == receipt["archive"]["sha256"]
assert sent["bytes"] == archive.stat().st_size
parts = root / "live_spool/private/objects"
raw = b"".join((parts / (sent["object"] + f".part{i:02d}-of-04").replace("/", "_")).read_bytes() for i in range(4))
assert raw == archive.read_bytes()
put(root / "RESULT.json", dict(status="PASS", pass_once_calls=1, synthetic=True, native_training=False,
    done=str(done), marker_sha256=identity, archive_sha256=sent["sha256"], copied_bytes=sent["bytes"], source=evidence))
print("PASS: shipped copier, one pass_once, marker/archive pins and all four local parts match; " + str(done))
