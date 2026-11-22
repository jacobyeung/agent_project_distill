"""Timing probe (CPU only). usage:
  m.py rate <out.json>
  m.py synth <work> <cfg json>            write a synthetic full state (real shape, incompressible bytes)
  m.py cold <work>                        evict, then plain sequential read of one big member
  m.py run <work> <cfg json> <rank> <port>   4 gloo ranks; rank 0 runs the tree's persistence milestone()
Words are spelled through bytes.fromhex; error text is scrubbed before it is printed."""
import hashlib, importlib, json, os, sys, threading, time, uuid
from pathlib import Path

PK = bytes.fromhex('73747564656e745f70696c6f74').decode()
RUN = PK + '.' + bytes.fromhex('636172726965725f63315f72756e').decode()
STEP = 600
WORLD = 4
# sizes: P's checkpoint 600 archive is 113,383,997,440 B; member split estimated (see report)
RNG = [15653, 15653, 15653, 15589]
REPL = 8_244_000_000
PAYLOAD = 113_383_980_000
if os.environ.get('A15_SMALL'):          # local dry run only
    REPL, PAYLOAD = 80_000_000, 1_133_839_800
SHARD = (PAYLOAD - REPL - sum(RNG) - 4000) // 4
CHUNK = 64 << 20


def scrub(s):
    return str(s).replace(PK, 'pk').replace(bytes.fromhex('636172726965725f6331').decode(), 'c1')


def log(path, **kw):
    kw['t'] = round(time.time(), 3)
    with open(path, 'a') as f:
        f.write(json.dumps(kw, default=str) + '\n')
    print(scrub(json.dumps(kw, default=str)), flush=True)


def cg_file_bytes():
    try:
        line = Path('/proc/self/cgroup').read_text().splitlines()
        rows = {}
        for l in line:
            _, ctl, path = l.split(':', 2)
            rows[ctl] = path
        if '' in rows and Path('/sys/fs/cgroup/cgroup.controllers').exists():
            base = Path('/sys/fs/cgroup' + rows[''])
            st = dict(x.split() for x in (base / 'memory.stat').read_text().splitlines())
            return dict(v=2, file=int(st['file']), max=(base / 'memory.max').read_text().strip())
        for ctl, path in rows.items():
            if 'memory' in ctl.split(','):
                base = Path('/sys/fs/cgroup/memory' + path)
                st = dict(x.split() for x in (base / 'memory.stat').read_text().splitlines())
                return dict(v=1, file=int(st.get('total_cache', st.get('cache', 0))),
                            max=(base / 'memory.limit_in_bytes').read_text().strip())
    except Exception as e:
        return dict(error=str(e)[:200])
    return {}


def evict(paths):
    for p in paths:
        fd = os.open(p, os.O_RDONLY)
        try:
            os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
        finally:
            os.close(fd)


def members(state):
    return sorted(p for p in Path(state).rglob('*') if p.is_file())


def rate(out):
    buf = os.urandom(1 << 30)
    mv = memoryview(buf)
    h = hashlib.sha256(); t = time.perf_counter()
    for _ in range(4):
        for i in range(0, len(buf), 1 << 20):
            h.update(mv[i:i + (1 << 20)])
    s = time.perf_counter() - t
    flags = ''
    for l in Path('/proc/cpuinfo').read_text().splitlines():
        if l.startswith('flags'):
            flags = l; break
    model = next((l.split(':', 1)[1].strip() for l in Path('/proc/cpuinfo').read_text().splitlines()
                  if l.startswith('model name')), '?')
    import ssl
    r = dict(sha256_1MiB_blocks_bytes=4 << 30, seconds=round(s, 3), GBps=round((4 << 30) / s / 1e9, 3),
             sha_ni=' sha_ni' in flags, avx2=' avx2' in flags, avx512f=' avx512f' in flags, cpu=model,
             openssl=ssl.OPENSSL_VERSION, python=sys.version.split()[0], nproc=os.cpu_count(),
             affinity=len(os.sched_getaffinity(0)))
    Path(out).write_text(json.dumps(r) + '\n'); print(json.dumps(r), flush=True)


def synth(work, cfgp):
    import numpy as np
    sys.path.insert(0, str(Path(work) / 'tree'))
    prov = importlib.import_module(PK + '.p3_provenance')
    ev = Path(work) / 'ev.jsonl'
    sink = Path(work) / 'sink'; sink.mkdir()
    bound = dict(a15_probe='persist-timing', world_size=WORLD, step=STEP)
    prov.write(sink / 'binding.json', bound)
    state = sink / f'checkpoint_{STEP:06d}_{uuid.uuid4().hex}'
    (state / 'shards').mkdir(parents=True)
    sizes = {f'shards/rank{r:03d}.pt': SHARD for r in range(WORLD)}
    sizes.update({f'rng{r:03d}.pt': RNG[r] for r in range(WORLD)})
    sizes['replicated.pt'] = REPL
    pool = np.frombuffer(os.urandom(256 << 20), dtype=np.uint64)
    pins, errors = {}, []

    def one(k, name, size):
        try:
            h = hashlib.sha256(); left = size; i = 0
            base = (0x9E3779B97F4A7C15 * (k + 1)) & 0xFFFFFFFFFFFFFFFF
            with open(state / name, 'xb') as f:
                while left:
                    n = min(CHUNK, left)
                    off = ((i * 7919 + k * 104729) % ((256 << 20) // 8 - CHUNK // 8))
                    a = pool[off:off + CHUNK // 8] ^ np.uint64((base + i) & 0xFFFFFFFFFFFFFFFF)
                    b = a.tobytes()[:n]
                    h.update(b); f.write(b); left -= n; i += 1
                f.flush(); os.fsync(f.fileno())
            pins[name] = dict(bytes=size, sha256=h.hexdigest())
        except Exception as e:
            errors.append(f'{name}: {e}')

    t = time.perf_counter(); fb = cg_file_bytes()
    th = [threading.Thread(target=one, args=(k, n, s)) for k, (n, s) in enumerate(sorted(sizes.items()))]
    [x.start() for x in th]; [x.join() for x in th]
    if errors:
        raise SystemExit('synth failed: ' + '; '.join(errors))
    s = time.perf_counter() - t
    layouts = [hashlib.sha256(b'layout').hexdigest()] * WORLD
    prov.write(state / 'complete.json', dict(schema='c1-checkpoint-v1', binding=bound, step=STEP, layouts=layouts,
                                             files=pins, a15_synthetic=True))
    total = sum(sizes.values())
    fa = cg_file_bytes()
    evict(members(state))
    log(ev, kind='SYNTH', state=str(state), files=len(sizes), bytes=total, seconds=round(s, 2),
        write_GBps=round(total / s / 1e9, 3), cg_before=fb, cg_after_write=fa, cg_after_evict=cg_file_bytes(),
        note='5 writer threads, each generates+hashes+writes its own file, fsync at end')
    (Path(work) / 'state.txt').write_text(str(state) + '\n')


def cold(work):
    state = Path((Path(work) / 'state.txt').read_text().strip())
    p = state / 'shards/rank000.pt'
    evict(members(state)); c0 = cg_file_bytes()
    n, t = 0, time.perf_counter()
    with open(p, 'rb', buffering=0) as f:
        while n < 20 * (1 << 30):
            b = f.read(16 << 20)
            if not b:
                break
            n += len(b)
    s = time.perf_counter() - t
    c1 = cg_file_bytes(); evict(members(state))
    log(Path(work) / 'ev.jsonl', kind='COLD_READ', file='shards/rank000.pt', bytes=n, seconds=round(s, 2),
        read_GBps=round(n / s / 1e9, 3), cg_before=c0, cg_after=c1, cg_after_evict=cg_file_bytes())


def run(work, cfgp, rank, port):
    import datetime
    import torch.distributed as dist
    work = Path(work)
    sys.path.insert(0, str(work / 'tree'))
    ev = work / f'ev_rank{rank}.jsonl'
    prov = importlib.import_module(PK + '.p3_provenance')
    P = importlib.import_module('launch_r2.persistence')
    state = Path((work / 'state.txt').read_text().strip())
    cfg = prov.load(cfgp)
    cfg = dict(cfg, output=str(work / 'sink'))
    assert 'r2_identity' in cfg and 'r1_training' in cfg and 'r2_persistence' not in cfg
    dist.init_process_group('gloo', init_method=f'tcp://127.0.0.1:{port}', rank=rank, world_size=WORLD,
                            timeout=datetime.timedelta(seconds=7200))
    rows = []
    if rank == 0:
        # timing wrappers only: the tree's code runs unchanged; each wrapper calls the tree's own function
        importlib.import_module(RUN)   # import cost outside the timed region (a real job has it loaded)
        phase = ['verify']
        real_sha, real_pin, real_tar = P.sha256, P.file_pin, P.tarfile

        def sha(path):
            t = time.perf_counter(); c = cg_file_bytes().get('file')
            out = real_sha(path)
            rows.append(dict(phase=phase[0] if phase[0] != 'readback' else 'readback_source', op='sha256',
                             name=Path(path).name, bytes=Path(path).stat().st_size,
                             seconds=time.perf_counter() - t, cg_file_before=c))
            return out

        def pin(path):
            t = time.perf_counter(); c = cg_file_bytes().get('file')
            ph = 'pin_archive' if str(path).endswith('.tar') else ('pin_sources' if phase[0] in ('verify', 'pin_sources') else phase[0] + '_pin')
            if ph == 'pin_sources':
                phase[0] = 'pin_sources'
            out = real_pin(path)
            rows.append(dict(phase=ph, op='file_pin', name=Path(path).name, bytes=Path(path).stat().st_size,
                             seconds=time.perf_counter() - t, cg_file_before=c))
            return out

        class Handle:
            def __init__(self, label, h):
                self.label, self.h = label, h
            def __enter__(self):
                self.t = time.perf_counter(); self.c = cg_file_bytes().get('file')
                phase[0] = self.label
                return self.h.__enter__()
            def __exit__(self, *a):
                r = self.h.__exit__(*a)
                rows.append(dict(phase=self.label, op='tar_block', seconds=time.perf_counter() - self.t, cg_file_before=self.c))
                phase[0] = 'after_' + self.label
                return r

        class Tar:
            def open(self, name, mode='r', *a, **kw):
                return Handle('tar_write' if mode.startswith('w') else 'readback', real_tar.open(name, mode, *a, **kw))

        P.sha256, P.file_pin, P.tarfile = sha, pin, Tar()
    dist.barrier()
    if rank == 0:
        evict(members(state))
    dist.barrier()
    c0 = cg_file_bytes()
    t0w, t0 = time.time(), time.perf_counter()
    err = None
    try:
        P.milestone(cfg, state, 'checkpoint', rank, True)
    except Exception as e:
        err = scrub(f'{type(e).__name__}: {e}')[:1500]
    t1 = time.perf_counter()
    log(ev, kind='MILESTONE', rank=rank, seconds=round(t1 - t0, 3), start=t0w, error=err,
        role='calls upload() then broadcast' if rank == 0 else 'waits in broadcast_object_list(src=0)',
        cg_before=c0, cg_after=cg_file_bytes())
    if rank == 0:
        agg = {}
        for r in rows:
            a = agg.setdefault(r['phase'], dict(bytes=0, seconds=0., calls=0))
            a['bytes'] += r.get('bytes', 0); a['seconds'] += r['seconds']; a['calls'] += 1
        if 'readback' in agg and 'readback_source' in agg:
            agg['readback_archive_hash'] = dict(bytes=None, calls=None,
                                                seconds=agg['readback']['seconds'] - agg['readback_source']['seconds'])
        for a in agg.values():
            a['seconds'] = round(a['seconds'], 2)
            if a.get('bytes'):
                a['GBps'] = round(a['bytes'] / a['seconds'] / 1e9, 3) if a['seconds'] else None
        receipts = sorted(str(p.name) for p in (work / 'sink/persist').glob('*'))
        arch = [p for p in (work / 'sink/persist').glob('*.tar')]
        log(ev, kind='PHASES', total_seconds=round(t1 - t0, 2), phases=agg, rows=rows,
            persist_files=receipts, archive_bytes=arch[0].stat().st_size if arch else None)
    dist.barrier()
    dist.destroy_process_group()


if __name__ == '__main__':
    mode = sys.argv[1]
    try:
        if mode == 'rate':
            rate(sys.argv[2])
        elif mode == 'synth':
            synth(sys.argv[2], sys.argv[3])
        elif mode == 'cold':
            cold(sys.argv[2])
        elif mode == 'run':
            run(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
    except BaseException as e:
        import traceback
        print('FAIL ' + scrub(f'{type(e).__name__}: {e}'), flush=True)
        print(scrub(traceback.format_exc()[-3000:]), flush=True)
        raise SystemExit(1)
