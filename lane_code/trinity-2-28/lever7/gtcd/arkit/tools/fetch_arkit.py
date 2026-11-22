"""Governed ARKit range fetcher: writes a tar stream to stdout (the governed pipe ends in ratelimit.py | tar xf -).
One HTTP(S) connection at a time, one range request at a time. Per capture in id order: the zip tail (wa.py's 70,000-byte
suffix), its central directory, then one range per picked member (wa.py's bound: local header .. +30+name+csize+1024),
each in member-offset order. Picks follow wa.py: nearest member by name timestamp, 2 ms traj tolerance.
Tar layout: <id>/_tail.bin, <id>/_cd.bin, <id>/_picks.json, <id>/m/<member basename>.bin (raw range bytes), and last
_FETCH_DONE.json. A failed request leaves its cause in ERRFILE and on stderr, waits 60 s and is retried once on a fresh
connection; a second failure ends the stream with exit 3 (no loop). Nothing is retried after that.
usage: fetch_arkit.py PLAN_ARKIT.json ERRFILE"""
import http.client, io, json, os, re, sys, tarfile, time
from urllib.parse import urlparse
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import zipcd

UA = 'Python-http.client'
TOL_TRAJ, TOL_INTERP = 0.002, 0.0105
TAIL = 70000
RETRY_WAIT = 60
IDLE_RECONNECT = 20      # a keep-alive connection idle this long (e.g. while the limiter floors the pipe) is reopened first
ERRFILE = None


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def cause(**kw):
    rec = dict(time=utc(), pid=os.getpid(), **kw)
    line = json.dumps(rec)
    print(line, file=sys.stderr, flush=True)
    if ERRFILE:
        with open(ERRFILE, 'a') as f:
            f.write(line + '\n')


class Fetcher:
    def __init__(self):
        self.c = None; self.host = None; self.last = 0.0; self.requests = 0; self.bytes = 0

    def close(self):
        if self.c is not None:
            try:
                self.c.close()
            except Exception:
                pass
        self.c = None

    def _conn(self, u):
        if self.c is not None and (self.host != (u.scheme, u.netloc) or time.monotonic() - self.last > IDLE_RECONNECT):
            self.close()
        if self.c is None:
            cls = http.client.HTTPSConnection if u.scheme == 'https' else http.client.HTTPConnection
            self.c = cls(u.netloc, timeout=60); self.host = (u.scheme, u.netloc)
        return self.c

    def _once(self, url, a, b):
        """bytes a..b inclusive (a < 0: suffix of -a bytes). Returns (data, total size)."""
        u = urlparse(url)
        rng = 'bytes=%d' % a if a < 0 else 'bytes=%d-%d' % (a, b)
        c = self._conn(u)
        c.request('GET', u.path, headers={'Range': rng, 'User-Agent': UA, 'Connection': 'keep-alive', 'Accept-Encoding': 'identity'})
        r = c.getresponse()
        cr = r.getheader('Content-Range') or ''
        if r.status != 206:
            self.close()   # never read a non-206 body (a 200 would be the whole archive)
            raise RuntimeError('http %d %s (range %s)' % (r.status, r.reason, rng))
        m = re.match(r'bytes (\d+)-(\d+)/(\d+)$', cr)
        if not m:
            self.close(); raise RuntimeError('bad Content-Range %r (range %s)' % (cr, rng))
        lo, hi, total = map(int, m.groups())
        want_lo = total + a if a < 0 else a
        want_hi = total - 1 if a < 0 else min(b, total - 1)
        if (lo, hi) != (want_lo, want_hi):
            self.close(); raise RuntimeError('Content-Range %r does not match %s' % (cr, rng))
        data = r.read()
        if len(data) != hi - lo + 1:
            self.close(); raise RuntimeError('short body %d of %d (range %s)' % (len(data), hi - lo + 1, rng))
        self.last = time.monotonic(); self.requests += 1; self.bytes += len(data)
        return data, total

    def get(self, url, a, b, what):
        try:
            return self._once(url, a, b)
        except Exception as e:
            self.close()
            cause(event='REQUEST_FAILED', attempt=1, what=what, url=url, range=[a, b], error=repr(e)[:300], next='retry once after %d s' % RETRY_WAIT)
        time.sleep(RETRY_WAIT)
        try:
            return self._once(url, a, b)
        except Exception as e:
            self.close()
            cause(event='REQUEST_FAILED', attempt=2, what=what, url=url, range=[a, b], error=repr(e)[:300], next='stream fails, exit 3')
            raise SystemExit(3)


def add(tf, name, data):
    ti = tarfile.TarInfo(name); ti.size = len(data); ti.mtime = int(time.time()); ti.mode = 0o644
    tf.addfile(ti, io.BytesIO(data))


def main():
    global ERRFILE
    plan_p, ERRFILE = sys.argv[1], sys.argv[2]
    plan = json.load(open(plan_p))['captures']
    f = Fetcher(); t0 = time.monotonic(); done = []
    cause(event='START', captures=len(plan), members=sum(len(e['need']) for e in plan.values()))
    tf = tarfile.open(fileobj=sys.stdout.buffer, mode='w|', format=tarfile.USTAR_FORMAT)
    for cid in sorted(plan):
        e = plan[cid]; url = e['u']
        tail, total = f.get(url, -TAIL, None, cid + ' tail')
        n_ent, cd_size, cd_off = zipcd.eocd(tail)
        if cd_off + cd_size > total or cd_size > 8 << 20:
            cause(event='BAD_EOCD', capture=cid, cd_off=cd_off, cd_size=cd_size, total=total); raise SystemExit(4)
        cd, _ = f.get(url, cd_off, cd_off + cd_size - 1, cid + ' cd')
        add(tf, cid + '/_tail.bin', tail); add(tf, cid + '/_cd.bin', cd)
        fr = zipcd.frames_of(zipcd.parse_cd(cd)); ts = np.array([x[0] for x in fr])
        picks, misses = [], []
        for k, t, flag in e['need']:
            b = zipcd.nearest(ts, t)
            tol = TOL_TRAJ if flag else TOL_INTERP
            if b is None or abs(ts[b] - t) > tol:
                misses.append([k, None if b is None else round(float(ts[b] - t) * 1000, 2)]); continue
            picks.append([k, b, fr[b][1], round(float(ts[b] - t) * 1000, 3)])
        add(tf, cid + '/_picks.json', json.dumps(dict(id=cid, url=url, rot=e['rot'], zip_bytes=total, cd_off=cd_off, cd_size=cd_size,
                                                      png_members=len(fr), picks=picks, misses=misses)).encode())
        nbytes = 0
        for b in sorted({p[1] for p in picks}, key=lambda b: fr[b][4]):
            a, z = zipcd.member_range(fr[b])
            data, _ = f.get(url, a, min(z, total - 1), '%s member %s' % (cid, fr[b][1]))
            if data[:4] != b'PK\x03\x04':
                cause(event='BAD_LOCAL_HEADER', capture=cid, member=fr[b][1]); raise SystemExit(4)
            add(tf, '%s/m/%s.bin' % (cid, os.path.basename(fr[b][1])), data); nbytes += len(data)
        rec = dict(id=cid, picks=len(picks), misses=len(misses), member_bytes=nbytes, cd_bytes=len(cd), seconds=round(time.monotonic() - t0, 1))
        done.append(rec); cause(event='CAPTURE_DONE', **rec)
    fin = dict(time=utc(), captures=done, requests=f.requests, bytes=f.bytes, seconds=round(time.monotonic() - t0, 1))
    add(tf, '_FETCH_DONE.json', json.dumps(fin).encode())
    tf.close(); sys.stdout.buffer.flush()
    f.close(); cause(event='END', requests=f.requests, bytes=f.bytes)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as e:
        cause(event='FETCHER_DIED', error=repr(e)[:500]); sys.exit(5)
