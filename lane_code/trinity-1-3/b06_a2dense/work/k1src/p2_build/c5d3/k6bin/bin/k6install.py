#!/usr/bin/env python3
"""Install the k6tk frame store (stdlib only).

usage: k6install.py --root ROOT --src DIR [DIR ...] [--meta DIR] [--sample N] [--verify-shards] [--seed S]
  ROOT    node-local root; frames land in ROOT/data2root/k6tk/<xx>/<sha>.png (rows cite /data2/k6tk/...;
          map /data2 -> ROOT/data2root).
  --src   directories holding the shard tars (<tag>_<nnn>.tar) or their GCS parts (<tag>_<nnn>.tar.partKK-of-NN);
          searched non-recursively plus one level of subdirectories.
  --meta  directory with INDEX.json and MAP.jsonl.gz (default: first --src dir).
Checks: every shard named in INDEX.json is found (sha256 checked with --verify-shards), every MAP path exists after
extraction, and the sha256 of N sampled MAP files (default 2000) matches. Exit 0 only if every check passes.
Writes ROOT/data2root/k6tk/INSTALL_OK.json on success."""
import argparse, gzip, hashlib, json, os, random, re, sys, tarfile, time


def find(srcs, name):
    for d in srcs:
        for base in [d] + [os.path.join(d, s) for s in sorted(os.listdir(d)) if os.path.isdir(os.path.join(d, s))]:
            p = os.path.join(base, name)
            if os.path.isfile(p):
                return [p]
            parts = sorted(n for n in os.listdir(base) if re.fullmatch(re.escape(name) + r"\.part\d+-of-\d+", n))
            if parts:
                nn = int(parts[0].rsplit("-of-", 1)[1])
                if len(parts) == nn:
                    return [os.path.join(base, n) for n in parts]
    return None


class Cat:
    """Read-only stream over concatenated files."""
    def __init__(self, paths):
        self.paths, self.i, self.f = list(paths), 0, open(paths[0], "rb")

    def read(self, n=-1):
        out = b""
        while n < 0 or len(out) < n:
            b = self.f.read(-1 if n < 0 else n - len(out))
            if b:
                out += b
                continue
            self.f.close(); self.i += 1
            if self.i >= len(self.paths):
                break
            self.f = open(self.paths[self.i], "rb")
        return out


def sha_of(paths):
    h = hashlib.sha256()
    for p in paths:
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(16 << 20), b""):
                h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--src", nargs="+", required=True)
    ap.add_argument("--meta")
    ap.add_argument("--sample", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--verify-shards", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    meta = a.meta or a.src[0]
    idx = json.load(open(os.path.join(meta, "INDEX.json")))
    dst = os.path.join(a.root, "data2root", "k6tk")
    os.makedirs(dst, exist_ok=True)
    rep = {"shards": len(idx["shards"]), "extracted_members": 0, "bad": []}
    for s in idx["shards"]:
        ps = find(a.src, s["name"])
        if not ps:
            rep["bad"].append(["shard not found", s["name"]]); continue
        if a.verify_shards and sha_of(ps) != s["sha256"]:
            rep["bad"].append(["shard sha256 mismatch", s["name"]]); continue
        n = 0
        with tarfile.open(fileobj=Cat(ps), mode="r|") as tf:
            for ti in tf:
                if not ti.isfile() or not re.fullmatch(r"[0-9a-f]{2}/[0-9a-f]{64}\.png", ti.name):
                    rep["bad"].append(["unexpected member", s["name"], ti.name]); continue
                out = os.path.join(dst, ti.name)
                os.makedirs(os.path.dirname(out), exist_ok=True)
                data = tf.extractfile(ti).read()
                tmp = out + ".tmp"
                with open(tmp, "wb") as f:
                    f.write(data)
                os.replace(tmp, out)
                n += 1
        if n != s["n"]:
            rep["bad"].append(["member count", s["name"], n, s["n"]])
        rep["extracted_members"] += n
        print(f"{s['name']}: {n} members ({time.time() - t0:.0f}s)", flush=True)
    rows = [json.loads(l) for l in gzip.open(os.path.join(meta, "MAP.jsonl.gz"), "rt")]
    missing = [r["path"] for r in rows if not os.path.isfile(os.path.join(dst, r["path"].split("/data2/k6tk/", 1)[1]))]
    rep["map_lines"] = len(rows); rep["map_paths_missing"] = len(missing)
    if missing:
        rep["bad"].append(["map paths missing", len(missing), missing[:5]])
    random.seed(a.seed)
    samp = random.sample(rows, min(a.sample, len(rows)))
    badsha = 0
    for r in samp:
        p = os.path.join(dst, r["path"].split("/data2/k6tk/", 1)[1])
        if not os.path.isfile(p) or hashlib.sha256(open(p, "rb").read()).hexdigest() != r["sha256"]:
            badsha += 1
    rep["sampled"] = len(samp); rep["sample_sha_mismatch"] = badsha
    if badsha:
        rep["bad"].append(["sample sha mismatch", badsha])
    rep["seconds"] = round(time.time() - t0, 1)
    rep["ok"] = not rep["bad"]
    print(json.dumps(rep))
    if rep["ok"]:
        json.dump(rep, open(os.path.join(dst, "INSTALL_OK.json"), "w"))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
