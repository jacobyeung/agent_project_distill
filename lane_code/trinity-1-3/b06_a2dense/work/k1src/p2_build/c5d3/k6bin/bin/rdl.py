#!/usr/bin/env python3
"""Parallel ranged HTTP downloader (stdlib). Restartable via chunk bitmap; verifies sha256.
usage: rdl.py URL DEST EXPECTED_SIZE EXPECTED_SHA256 [threads] [chunk_mb]"""
import hashlib, json, os, sys, threading, time, urllib.request, queue
url, dest, size, sha = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
nth = int(sys.argv[5]) if len(sys.argv) > 5 else 16
csz = (int(sys.argv[6]) if len(sys.argv) > 6 else 64) << 20
if os.path.exists(dest + '.ok'):
    print('already ok', dest); sys.exit(0)
part = dest + '.part'; bm = dest + '.chunks'
n = (size + csz - 1) // csz
done = set(json.load(open(bm))) if os.path.exists(bm) else set()
fd = os.open(part, os.O_RDWR | os.O_CREAT, 0o644)
if os.fstat(fd).st_size != size:
    os.ftruncate(fd, size)
lock = threading.Lock(); q = queue.Queue()
for i in range(n):
    if i not in done: q.put(i)
print(f'{dest}: {n} chunks, {len(done)} done, {q.qsize()} todo', flush=True)
t0 = time.time(); got = [0]; errs = [0]
def save():
    tmp = bm + '.tmp'; json.dump(sorted(done), open(tmp, 'w')); os.replace(tmp, bm)
def work():
    while True:
        try: i = q.get_nowait()
        except queue.Empty: return
        a = i * csz; b = min(size, a + csz) - 1
        for att in range(8):
            try:
                req = urllib.request.Request(url, headers={'Range': f'bytes={a}-{b}', 'User-Agent': 'curl/8'})
                with urllib.request.urlopen(req, timeout=120) as r:
                    if r.status != 206: raise RuntimeError(f'status {r.status}')
                    off = a
                    while True:
                        buf = r.read(4 << 20)
                        if not buf: break
                        os.pwrite(fd, buf, off); off += len(buf)
                    if off != b + 1: raise RuntimeError(f'short {off} vs {b+1}')
                with lock:
                    done.add(i); got[0] += b + 1 - a
                    if len(done) % 16 == 0:
                        save(); el = time.time() - t0
                        print(f'{len(done)}/{n} {got[0]/el/1e6:.0f} MB/s', flush=True)
                break
            except Exception as e:
                with lock: errs[0] += 1
                print(f'chunk {i} att {att} err {e!r}', flush=True); time.sleep(2 + 3 * att)
        else:
            print(f'chunk {i} FAILED', flush=True)
ts = [threading.Thread(target=work) for _ in range(nth)]
[t.start() for t in ts]; [t.join() for t in ts]
save(); os.fsync(fd); os.close(fd)
if len(done) != n:
    print('INCOMPLETE', len(done), n); sys.exit(2)
print(f'download done {time.time()-t0:.0f}s; hashing', flush=True)
h = hashlib.sha256()
with open(part, 'rb') as f:
    while True:
        buf = f.read(16 << 20)
        if not buf: break
        h.update(buf)
if h.hexdigest() != sha:
    print('SHA MISMATCH', h.hexdigest()); os.replace(bm, bm + '.bad'); sys.exit(3)
os.replace(part, dest); open(dest + '.ok', 'w').write(sha + '\n')
print('OK', dest, sha, f'{time.time()-t0:.0f}s', flush=True)
