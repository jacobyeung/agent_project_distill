"""Range-fetch new dense frames from Apple lowres_wide.zip with the unchanged k6 `wa.py` decoder.

usage: wa_dense.py WA_PY TASKS_A.json STORE OUT.jsonl THREADS [PARITY_EVERY]
TASKS_A (from dense_manifest.py plan): {token: {"u": zip url, "rot": ..., "need_ordinals": [k...],
                                                "known": [[k, t, flag], ...]}}
Per capture:
  1. GET <capture>/lowres_wide.traj (whole file). Row k's first column is ordinal k's timestamp: this is the
     k6 clock (checked on Orchard 2026-11-16: 167 of 167 known ordinals of 2 captures equal traj rows to 1e-5).
  2. Refuse the capture unless every known flag-1 ordinal equals its traj row within 1e-5 s and every needed
     ordinal is < number of traj rows.
  3. Parity: add known ordinals as parity targets (2 per capture; all 32 for every PARITY_EVERY-th capture);
     their output sha256 must equal the pinned sha256 (store pins live in the k6 map; the job compares).
  4. Call wa.do_scene with need = [[k, traj[k], 1]] (tolerance 2 ms, member nearest in time), unchanged.
The decoder library versions are asserted before any request (k6 used opencv-python-headless 4.14.0.94,
numpy 2.2.6, Python 3.12.3); a different version stops the job, because byte pins broke on 40% of ARKit frames
across versions. Output lines carry tokens only.
"""
import importlib.util
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

PINNED = {'cv2': '4.14.0', 'numpy': '2.2.6', 'python': '3.12.3'}


def load_wa(path):
    spec = importlib.util.spec_from_file_location('wa', path)
    wa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wa)
    return wa


def check_versions(wa):
    got = {'cv2': wa.cv2.__version__, 'numpy': wa.np.__version__, 'python': sys.version.split()[0]}
    if got != PINNED:
        raise SystemExit('decoder versions differ from the k6 pins: ' + json.dumps(got))
    return got


def traj_times(wa, zip_url):
    u = urlparse(zip_url)
    base = zip_url.rsplit('/', 1)[0] + '/lowres_wide.traj'
    data = wa.get_range(base, 0, 50_000_000)
    rows = [line.split() for line in data.decode().splitlines() if line.strip()]
    return [float(r[0]) for r in rows], len(data)


def plan_capture(wa, tok, e, parity_all):
    ts, nbytes = traj_times(wa, e['u'])
    known = e['known']
    bad = [k for k, t, f in known if f == 1 and (k >= len(ts) or abs(ts[k] - t) > 1e-5)]
    if bad:
        return None, dict(s=tok, error='clock: known ordinals differ from traj rows', n_bad=len(bad))
    over = [k for k in e['need_ordinals'] if k >= len(ts)]
    if over:
        return None, dict(s=tok, error='ordinal past traj rows', n_over=len(over))
    known_k = sorted(k for k, t, f in known if f == 1)
    parity = known_k if parity_all else [known_k[0], known_k[len(known_k) // 2]]
    need = [[k, ts[k], 1] for k in sorted(set(e['need_ordinals']) | set(parity))]
    return dict(u=e['u'], rot=e['rot'], need=need), dict(traj_rows=len(ts), traj_bytes=nbytes, parity=parity)


def main():
    wa_path, tasks_p, store, out_p, threads = sys.argv[1:6]
    every = int(sys.argv[6]) if len(sys.argv) > 6 else 20
    wa = load_wa(wa_path)
    versions = check_versions(wa)
    tasks = json.load(open(tasks_p))
    done = set()
    if os.path.exists(out_p):
        for line in open(out_p):
            done.add(json.loads(line)['s'])
    toks = [t for t in sorted(tasks) if t not in done]
    for i in range(256):
        os.makedirs(os.path.join(store, f'{i:02x}'), exist_ok=True)
    lock, stats, t0 = threading.Lock(), dict(ok=0, err=0, frames=0, misses=0, fetched=0), time.time()
    order = {t: n for n, t in enumerate(sorted(tasks))}

    def work(tok):
        try:
            entry, meta = plan_capture(wa, tok, tasks[tok], order[tok] % every == 0)
            if entry is None:
                r = meta
            else:
                r = wa.do_scene(tok, entry, store, '/data2/k6dx')
                r.update(meta)
        except Exception as ex:  # one capture's failure is recorded, never retried here
            r = dict(s=tok, error=repr(ex)[:200])
        with lock:
            with open(out_p, 'a') as fh:
                fh.write(json.dumps(r) + '\n')
            if 'error' in r:
                stats['err'] += 1
            else:
                stats['ok'] += 1
                stats['frames'] += len(r['frames'])
                stats['misses'] += len(r['misses'])
                stats['fetched'] += r['fetched']
            n = stats['ok'] + stats['err']
            if n % 25 == 0 or n == len(toks):
                print(json.dumps(dict(t=round(time.time() - t0), done=n, of=len(toks), **stats)), flush=True)

    print(json.dumps(dict(versions=versions, captures=len(toks))), flush=True)
    with ThreadPoolExecutor(int(threads)) as ex:
        list(ex.map(work, toks))
    print('END', json.dumps(stats), flush=True)


if __name__ == '__main__':
    main()
