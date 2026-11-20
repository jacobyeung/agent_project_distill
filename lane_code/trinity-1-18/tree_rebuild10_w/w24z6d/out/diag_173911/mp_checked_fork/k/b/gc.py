import sys, http.client
sys.path.insert(0,'/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z6d/out/diag_173911')
from strict_sink import Connection
if http.client.HTTPSConnection.__module__ == 'http.client': http.client.HTTPSConnection=Connection
#!/usr/bin/env python3
"""Orchard side GCS writer (stdlib only; no Google credential on Orchard).
Uploads to resumable-upload session URIs that Trinity minted (rt/GCS_HOWTO.md). Each session URI writes exactly one
object name and stays valid for about a week.
usage:
  gcsput.py put SESSIONS_JSON NAME FILE               one object NAME <- FILE
  gcsput.py split SESSIONS_JSON NAME FILE NPARTS [P]  objects NAME.partKK-of-NN <- byte ranges of FILE, P in parallel
                                                      (default P = NPARTS); restore = concatenate the parts in order
  gcsput.py names NAME NPARTS                         print the part names to mint for `split`
Each finished object appends one JSON line to SESSIONS_JSON + ".receipts.jsonl": name, bytes, md5 (checked against the
md5Hash GCS reports), sha256 of the bytes, offset, seconds. A part already in the receipts with the same size is skipped,
so a rerun resumes. Exit 1 on any failure.
"""
import base64, hashlib, http.client, json, os, sys, time, urllib.parse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
CHUNK = 16 << 20
def part_names(name, nparts):
    return [f"{name}.part{k:02d}-of-{nparts:02d}" for k in range(nparts)]
def upload(uri, path, offset, length, name):
    """PUT bytes [offset, offset+length) of path to the session URI in one request; verify GCS's md5Hash."""
    started = time.time()
    url = urllib.parse.urlsplit(uri)
    md5, sha = hashlib.md5(), hashlib.sha256()
    for attempt in range(1):
        try:
            conn = http.client.HTTPSConnection(url.netloc, timeout=600)
            conn.putrequest("PUT", url.path + "?" + url.query)
            conn.putheader("Content-Length", str(length))
            conn.putheader("Content-Type", "application/octet-stream")
            conn.endheaders()
            md5, sha = hashlib.md5(), hashlib.sha256()
            with open(path, "rb") as stream:
                stream.seek(offset)
                left = length
                while left:
                    block = stream.read(min(CHUNK, left))
                    if not block:
                        raise IOError(f"short read at {offset + length - left}")
                    md5.update(block)
                    sha.update(block)
                    conn.send(block)
                    left -= len(block)
            reply = conn.getresponse()
            body = reply.read()
            if reply.status not in (200, 201):
                raise IOError(f"HTTP {reply.status}: {body[:300]!r}")
            meta = json.loads(body)
            if int(meta["size"]) != length or meta.get("md5Hash") != base64.b64encode(md5.digest()).decode():
                raise IOError(f"GCS size/md5 mismatch for {name}: {meta.get('size')} {meta.get('md5Hash')}")
            return {"name": name, "bytes": length, "offset": offset, "md5": meta["md5Hash"], "sha256": sha.hexdigest(),
                    "generation": meta.get("generation"), "seconds": round(time.time() - started, 1)}
        except Exception as error:  # a restarted single-request PUT on the same session starts over from byte 0
            sys.stderr.write(f"gcsput: {name} attempt {attempt}: {type(error).__name__}: {error}\n")
            if attempt == 0:
                raise
            time.sleep(10 * (attempt + 1))
def done(receipts):
    out = {}
    if os.path.exists(receipts):
        for line in open(receipts):
            if line.strip():
                row = json.loads(line)
                out[row["name"]] = row
    return out
def main(argv):
    mode = argv[0]
    if mode == "names":
        print("\n".join(part_names(argv[1], int(argv[2]))))
        return 0
    sessions_path, name, path = argv[1], argv[2], argv[3]
    sessions = json.load(open(sessions_path))
    receipts = sessions_path + ".receipts.jsonl"
    size = os.path.getsize(path)
    if mode == "put":
        jobs = [(name, 0, size)]
        parallel = 1
    elif mode == "split":
        nparts = int(argv[4])
        parallel = int(argv[5]) if len(argv) > 5 else nparts
        step = -(-size // nparts)
        jobs = [(n, k * step, max(0, min(step, size - k * step))) for k, n in enumerate(part_names(name, nparts))]
    else:
        sys.exit(__doc__)
    prior = done(receipts)
    todo = [j for j in jobs if not (j[0] in prior and prior[j[0]]["bytes"] == j[2] and prior[j[0]]["offset"] == j[1])]
    missing = [j[0] for j in todo if j[0] not in sessions]
    if missing:
        sys.exit(f"gcsput: no session URI for {missing[:3]} ({len(missing)} missing); mint them on Trinity")
    started, failed = time.time(), 0
    try:  # processes (fastest); threads where the host has no room for semaphores (Orchard login /dev/shm)
        pool = ProcessPoolExecutor(max_workers=max(1, parallel)) if parallel > 1 and len(todo) > 1 else ThreadPoolExecutor(1)
    except OSError:
        pool = ThreadPoolExecutor(max_workers=max(1, parallel))
    with pool:
        futures = [(j, pool.submit(upload, sessions[j[0]], path, j[1], j[2], j[0])) for j in todo]
        for job, future in futures:
            try:
                row = future.result()
            except Exception as error:
                failed += 1
                sys.stderr.write(f"gcsput: FAILED {job[0]}: {error}\n")
                continue
            row["file"] = os.path.abspath(path)
            with open(receipts, "a") as stream:
                stream.write(json.dumps(row, sort_keys=True) + "\n")
    seconds = time.time() - started
    moved = sum(j[2] for j in todo)
    print(json.dumps({"gcsput": mode, "name": name, "objects": len(jobs), "uploaded": len(todo) - failed, "failed": failed,
                      "bytes": moved, "seconds": round(seconds, 1),
                      "MBps": round(moved / max(seconds, 1e-3) / 1e6, 1)}), flush=True)
    return 1 if failed else 0
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
