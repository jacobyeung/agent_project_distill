"""Range-fetch selected frames from remote zip archives, orient, resize, store content-addressed PNGs.

usage: wa.py PLAN.json STORE_DIR STORE_PREFIX OUT.jsonl THREADS [SHARD NSHARDS]
PLAN: {token: {"u": url, "rot": "none|cw|ccw|180", "need": [[k, t, flag], ...]}}
Output: one JSON line per token; logs carry tokens only.
"""
import hashlib, http.client, json, os, struct, sys, threading, time, zlib
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
import numpy as np
import cv2

cv2.setNumThreads(1)
TOL_TRAJ = 0.002
TOL_INTERP = 0.0105
SCALE = 2.5
_local = threading.local()


def conn(host):
    c = getattr(_local, "c", None)
    if c is None or getattr(_local, "h", None) != host:
        c = http.client.HTTPSConnection(host, timeout=60)
        _local.c, _local.h = c, host
    return c


def get_range(url, a, b):
    """bytes a..b inclusive; a<0 means suffix."""
    u = urlparse(url)
    rng = f"bytes={a}" if a < 0 else f"bytes={a}-{b}"
    last = None
    for attempt in range(5):
        try:
            c = conn(u.netloc)
            c.request("GET", u.path, headers={"Range": rng, "Connection": "keep-alive"})
            r = c.getresponse()
            data = r.read()
            if r.status in (200, 206):
                return data
            last = f"http {r.status}"
            if r.status in (403, 404):
                break
        except Exception as e:
            last = repr(e)[:120]
            _local.c = None
        time.sleep(1 + 2 * attempt)
    raise RuntimeError("range failed: " + str(last))


def central_dir(url):
    tail = get_range(url, -70000, None)
    i = tail.rfind(b"PK\x05\x06")
    if i < 0:
        raise RuntimeError("no eocd")
    n_entries, cd_size, cd_off = struct.unpack("<HII", tail[i + 10:i + 20])
    if cd_off == 0xFFFFFFFF or n_entries == 0xFFFF:
        j = tail.rfind(b"PK\x06\x06")
        n_entries, cd_size, cd_off = struct.unpack("<QQQ", tail[j + 32:j + 56])
    total_tail_start = None
    cd = get_range(url, cd_off, cd_off + cd_size - 1)
    ents, p = [], 0
    while p + 46 <= len(cd) and cd[p:p + 4] == b"PK\x01\x02":
        method = struct.unpack("<H", cd[p + 10:p + 12])[0]
        csize, usize = struct.unpack("<II", cd[p + 20:p + 28])
        nl, el, cl = struct.unpack("<HHH", cd[p + 28:p + 34])
        lho = struct.unpack("<I", cd[p + 42:p + 46])[0]
        name = cd[p + 46:p + 46 + nl].decode("utf-8", "replace")
        extra = cd[p + 46 + nl:p + 46 + nl + el]
        if csize == 0xFFFFFFFF or usize == 0xFFFFFFFF or lho == 0xFFFFFFFF:
            q = 0
            while q + 4 <= len(extra):
                hid, hl = struct.unpack("<HH", extra[q:q + 4])
                if hid == 1:
                    vals = list(struct.unpack("<" + "Q" * (hl // 8), extra[q + 4:q + 4 + 8 * (hl // 8)]))
                    if usize == 0xFFFFFFFF: usize = vals.pop(0)
                    if csize == 0xFFFFFFFF: csize = vals.pop(0)
                    if lho == 0xFFFFFFFF: lho = vals.pop(0)
                q += 4 + hl
        ents.append((name, method, csize, lho, nl))
        p += 46 + nl + el + cl
    return ents


def stamp(name):
    b = os.path.basename(name)
    if not b.endswith(".png") or "_" not in b:
        return None
    try:
        return float(b[:-4].rpartition("_")[2])
    except ValueError:
        return None


def orient(img, rot):
    if rot == "cw":
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif rot == "ccw":
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif rot == "180":
        img = cv2.rotate(img, cv2.ROTATE_180)
    h, w = img.shape[:2]
    return cv2.resize(img, (int(round(w * SCALE)), int(round(h * SCALE))), interpolation=cv2.INTER_CUBIC)


def put(store, data):
    sha = hashlib.sha256(data).hexdigest()
    d = os.path.join(store, sha[:2])
    dst = os.path.join(d, sha + ".png")
    if not os.path.exists(dst):
        tmp = os.path.join(d, f".{sha}.{os.getpid()}.{threading.get_ident()}.tmp")
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, dst)
    return sha


def do_scene(tok, e, store, prefix, keep_raw=None):
    t_start = time.time()
    url, rot, need = e["u"], e["rot"], e["need"]
    ents = central_dir(url)
    frames = [(stamp(n), n, m, cs, lho, nl) for (n, m, cs, lho, nl) in ents]
    frames = sorted(f for f in frames if f[0] is not None)
    ts = np.array([f[0] for f in frames])
    picks, misses, fetched = [], [], 0
    for k, t, flag in need:
        j = int(np.searchsorted(ts, t))
        best = None
        for jj in (j - 1, j):
            if 0 <= jj < len(ts) and (best is None or abs(ts[jj] - t) < abs(ts[best] - t)):
                best = jj
        tol = TOL_TRAJ if flag else TOL_INTERP
        if best is None or abs(ts[best] - t) > tol:
            misses.append([k, None if best is None else round(float(ts[best] - t) * 1000, 2)])
            continue
        picks.append((k, best, float(ts[best] - t)))
    # coalesce member ranges
    order = sorted(set(b for _, b, _ in picks), key=lambda b: frames[b][4])
    groups, cur = [], []
    for b in order:
        a0 = frames[b][4]
        if cur and a0 - (frames[cur[-1]][4] + 30 + frames[cur[-1]][5] + frames[cur[-1]][3] + 1024) > 262144:
            groups.append(cur); cur = []
        cur.append(b)
    if cur:
        groups.append(cur)
    out_by_b = {}
    for g in groups:
        a = frames[g[0]][4]
        z = frames[g[-1]][4] + 30 + frames[g[-1]][5] + frames[g[-1]][3] + 1024
        buf = get_range(url, a, z)
        fetched += len(buf)
        for b in g:
            _, name, method, cs, lho, nl = frames[b]
            o = lho - a
            if buf[o:o + 4] != b"PK\x03\x04":
                raise RuntimeError("bad local header")
            n2, e2 = struct.unpack("<HH", buf[o + 26:o + 30])
            raw = buf[o + 30 + n2 + e2:o + 30 + n2 + e2 + cs]
            if method == 8:
                raw = zlib.decompressobj(-15).decompress(raw)
            img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                raise RuntimeError("decode failed")
            if keep_raw is not None:
                keep_raw[round(frames[b][0], 3)] = img
            img2 = orient(img, rot)
            ok, enc = cv2.imencode(".png", img2, [cv2.IMWRITE_PNG_COMPRESSION, 3])
            data = enc.tobytes()
            sha = put(store, data)
            out_by_b[b] = (sha, img2.shape[1], img2.shape[0], len(data), img.shape[1], img.shape[0])
    rows, nbytes = [], 0
    for k, b, dt in picks:
        sha, w, h, n, w0, h0 = out_by_b[b]
        rows.append([k, sha, w, h, round(dt * 1000, 3), round(frames[b][0], 3)])
        nbytes += n
    return {"s": tok, "frames": rows, "misses": misses, "n_members": len(frames),
            "first_ts": frames[0][0] if frames else None, "last_ts": frames[-1][0] if frames else None,
            "fetched": fetched, "requests": len(groups) + 2, "bytes": nbytes, "src_hw": [out_by_b[b][5], out_by_b[b][4]] if out_by_b else None,
            "sec": round(time.time() - t_start, 1)}


def main():
    plan_p, store, prefix, out_p, threads = sys.argv[1:6]
    shard, nsh = (int(sys.argv[6]), int(sys.argv[7])) if len(sys.argv) > 7 else (0, 1)
    plan = json.load(open(plan_p))
    toks = sorted(plan)[shard::nsh]
    done = set()
    if os.path.exists(out_p):
        for line in open(out_p):
            try:
                done.add(json.loads(line)["s"])
            except Exception:
                pass
    toks = [t for t in toks if t not in done]
    for i in range(256):
        os.makedirs(os.path.join(store, f"{i:02x}"), exist_ok=True)
    lock = threading.Lock()
    stats = {"ok": 0, "err": 0, "frames": 0, "misses": 0, "fetched": 0}
    t0 = time.time()

    def work(t):
        try:
            r = do_scene(t, plan[t], store, prefix)
        except Exception as ex:
            r = {"s": t, "error": repr(ex)[:200]}
        with lock:
            with open(out_p, "a") as f:
                f.write(json.dumps(r) + "\n")
            if "error" in r:
                stats["err"] += 1
            else:
                stats["ok"] += 1; stats["frames"] += len(r["frames"]); stats["misses"] += len(r["misses"]); stats["fetched"] += r["fetched"]
            n = stats["ok"] + stats["err"]
            if n % 25 == 0 or n == len(toks):
                print(json.dumps({"t": round(time.time() - t0), "done": n, "of": len(toks), **stats}), flush=True)

    with ThreadPoolExecutor(int(threads)) as ex:
        list(ex.map(work, toks))
    print("END", json.dumps(stats), flush=True)


if __name__ == "__main__":
    main()
