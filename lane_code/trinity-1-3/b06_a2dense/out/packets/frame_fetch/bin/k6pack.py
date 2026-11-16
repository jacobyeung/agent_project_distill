"""Pack a content-addressed store (<xx>/<sha>.png) into tar shards of <= MAXM members (members 'xx/sha.png').
usage: k6pack.py STORE OUTDIR TAG [MAXM]; writes OUTDIR/<TAG>_<nnn>.tar and OUTDIR/LIST.json"""
import hashlib, json, os, sys, tarfile
store, out, tag = sys.argv[1:4]
maxm = int(sys.argv[4]) if len(sys.argv) > 4 else 32000
os.makedirs(out, exist_ok=True)
files = []
for i in range(256):
    d = f"{i:02x}"
    p = os.path.join(store, d)
    if os.path.isdir(p):
        files += [d + "/" + n for n in sorted(os.listdir(p)) if n.endswith(".png") and not n.startswith(".")]
shards = []
for j in range(0, len(files), maxm):
    part = files[j:j + maxm]
    name = f"{tag}_{j // maxm:03d}.tar"
    tmp = os.path.join(out, "." + name + ".tmp")
    with tarfile.open(tmp, "w", format=tarfile.USTAR_FORMAT) as tf:
        for m in part:
            fp = os.path.join(store, m)
            ti = tarfile.TarInfo(m)
            ti.size = os.path.getsize(fp)
            ti.mode = 0o644
            ti.mtime = 0
            with open(fp, "rb") as f:
                tf.addfile(ti, f)
    h = hashlib.sha256()
    with open(tmp, "rb") as f:
        for b in iter(lambda: f.read(16 << 20), b""):
            h.update(b)
    os.replace(tmp, os.path.join(out, name))
    shards.append({"name": name, "n": len(part), "bytes": os.path.getsize(os.path.join(out, name)), "sha256": h.hexdigest(),
                   "first": part[0], "last": part[-1]})
    print(json.dumps(shards[-1]), flush=True)
json.dump({"tag": tag, "members": len(files), "shards": shards}, open(os.path.join(out, "LIST.json"), "w"), indent=1)
