"""Decode selected frames from local videos into content-addressed PNGs.

usage: wd.py MANIFEST.json.gz CONF.json STORE_DIR OUT.jsonl PROCS [SHARD NSHARDS]
MANIFEST["v"]: {token: {"g": group, "p": path | "n": name, "raw_n": N, "need": [idx, ...]}}
CONF: {"groups": {group: {"mode": "same" | "half", "out_wh": [w, h] | null}}, "subdir_root": {group: dir}}
Logs and outputs carry tokens only.
"""
import gzip, hashlib, json, os, sys, time
from multiprocessing import Pool
import numpy as np
import cv2

cv2.setNumThreads(1)
G = {}


def put(store, data):
    sha = hashlib.sha256(data).hexdigest()
    d = os.path.join(store, sha[:2])
    dst = os.path.join(d, sha + ".png")
    if not os.path.exists(dst):
        tmp = os.path.join(d, f".{sha}.{os.getpid()}.tmp")
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, dst)
    return sha


def resolve(e):
    if "p" in e:
        return e["p"]
    for root in G["roots"].get(e["g"], []):
        q = os.path.join(root, e["n"])
        if os.path.exists(q):
            return q
    return None


def one(item):
    tok, e = item
    t0 = time.time()
    try:
        conf = G["conf"]["groups"][e["g"]]
        p = resolve(e)
        if not p:
            return {"s": tok, "error": "no source"}
        cap = cv2.VideoCapture(p)
        fps = cap.get(cv2.CAP_PROP_FPS)
        meta_n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        want = {}
        for i in e["need"]:
            j = i // 2 if conf["mode"] == "half" else i
            want.setdefault(j, []).append(i)
        last = max(want)
        got, j = {}, 0
        while j <= last:
            if not cap.grab():
                break
            if j in want:
                ok, img = cap.retrieve()
                if ok and img is not None:
                    if conf.get("out_wh") and (img.shape[1], img.shape[0]) != tuple(conf["out_wh"]):
                        img = cv2.resize(img, tuple(conf["out_wh"]), interpolation=cv2.INTER_AREA)
                    ok, enc = cv2.imencode(".png", img, [cv2.IMWRITE_PNG_COMPRESSION, 3])
                    data = enc.tobytes()
                    got[j] = (put(G["store"], data), img.shape[1], img.shape[0], len(data))
            j += 1
        decoded = j
        frames, misses, nbytes = [], [], 0
        for jj, idxs in want.items():
            for i in idxs:
                if jj in got:
                    sha, w, h, n = got[jj]
                    frames.append([i, sha, w, h, jj])
                    nbytes += n
                else:
                    misses.append(i)
        return {"s": tok, "frames": sorted(frames), "misses": sorted(misses), "fps": fps, "meta_n": meta_n,
                "decoded_to": decoded, "raw_n": e.get("raw_n"), "bytes": nbytes, "sec": round(time.time() - t0, 1)}
    except Exception as ex:
        return {"s": tok, "error": repr(ex)[:200]}


def init(conf, store, roots):
    G["conf"], G["store"], G["roots"] = conf, store, roots
    cv2.setNumThreads(1)


def main():
    man_p, conf_p, store, out_p, procs = sys.argv[1:6]
    shard, nsh = (int(sys.argv[6]), int(sys.argv[7])) if len(sys.argv) > 7 else (0, 1)
    man = json.load(gzip.open(man_p, "rt"))["v"]
    conf = json.load(open(conf_p))
    roots = {}
    for g, base in conf.get("subdir_root", {}).items():
        roots[g] = [os.path.join(base, s) for s in sorted(os.listdir(base))]
    toks = sorted(t for t in man if man[t]["g"] in conf["groups"])[shard::nsh]
    done = set()
    if os.path.exists(out_p):
        for line in open(out_p):
            try:
                r = json.loads(line)
                if "error" not in r:
                    done.add(r["s"])
            except Exception:
                pass
    toks = [t for t in toks if t not in done]
    for i in range(256):
        os.makedirs(os.path.join(store, f"{i:02x}"), exist_ok=True)
    # big jobs first
    toks.sort(key=lambda t: -max(man[t]["need"]))
    st = {"ok": 0, "err": 0, "frames": 0, "misses": 0}
    t0 = time.time()
    with Pool(int(procs), initializer=init, initargs=(conf, store, roots)) as pool, open(out_p, "a") as f:
        for n, r in enumerate(pool.imap_unordered(one, [(t, man[t]) for t in toks]), 1):
            f.write(json.dumps(r) + "\n"); f.flush()
            if "error" in r:
                st["err"] += 1
            else:
                st["ok"] += 1; st["frames"] += len(r["frames"]); st["misses"] += len(r["misses"])
            if n % 25 == 0 or n == len(toks):
                print(json.dumps({"t": round(time.time() - t0), "done": n, "of": len(toks), **st}), flush=True)
    print("END", json.dumps(st), flush=True)


if __name__ == "__main__":
    main()
