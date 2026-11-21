"""Supervise one child; diagnostics never depend on its exception handler."""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import resource
import selectors
import signal
import subprocess
import sys
import time
import threading
from contextlib import contextmanager

TAIL = 16000
LOG_CAP = 262144
MEMORY_PEAKS = dict(peak_tree_rss_bytes=0, peak_cgroup_current_bytes=None,
                    cgroup_memory_peak_bytes=None, peak_guarded_bytes=0)


def tree_rss(pid=None, proc=Path('/proc')):
    """Sum current RSS over this process and descendants, including thread children."""
    pending = [os.getpid() if pid is None else pid]; seen = set(); total = 0
    while pending:
        pid = pending.pop()
        if pid in seen: continue
        seen.add(pid)
        try:
            for line in (proc/str(pid)/'status').read_text().splitlines():
                if line.startswith('VmRSS:'): total += int(line.split()[1])*1024
            for task in (proc/str(pid)/'task').iterdir():
                try: pending.extend(map(int, (task/'children').read_text().split()))
                except OSError: pass
        except OSError: pass
    return total


def guarded_memory(values, resident):
    try:
        stat = dict(line.split() for line in values['memory.stat'].splitlines())
        file_lru = int(stat['active_file']) + int(stat['inactive_file'])
        # v2 file includes shmem, but file LRUs normally exclude it. Only add
        # back overlap: blindly adding all shmem would count it twice.
        reclaimable = file_lru
        if 'file' in stat and 'shmem' in stat:
            reclaimable = min(file_lru, max(0, int(stat['file'])-int(stat['shmem'])))
        return max(0, int(values['memory.current'])-reclaimable), 'cgroup'
    except (KeyError, ValueError, TypeError):
        return resident, 'process_tree_rss'


def sample_memory():
    values = cgroup_memory(); resident = tree_rss()
    guarded, source = guarded_memory(values, resident)
    observations = dict(peak_tree_rss_bytes=resident, peak_guarded_bytes=guarded)
    for field, key in (('peak_cgroup_current_bytes', 'memory.current'),
                       ('cgroup_memory_peak_bytes', 'memory.peak')):
        try: observations[field] = int(values[key])
        except (KeyError, ValueError): pass
    for key, value in observations.items():
        MEMORY_PEAKS[key] = max(MEMORY_PEAKS[key] or 0, value)
    return dict(MEMORY_PEAKS, guarded_bytes=guarded, guard_source=source), values

def memory_limit(mode):
    return (150 if mode == "c" else 180)*1024**3

def memory_over(mode, strict=False):
    metrics, _ = sample_memory()
    return metrics['guarded_bytes'] >= memory_limit(mode)


class Streams:
    def __init__(self, directory, C):
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
        self.C = C; self.tails = [bytearray(), bytearray()]; self.counts = [0, 0]
        self.files = [(self.directory/name).open("xb") for name in ("8.log", "9.log")]
        self.over = False

    def feed(self, index, chunk):
        self.tails[index].extend(chunk); del self.tails[index][:-TAIL]
        retain = chunk[:max(0, LOG_CAP-self.counts[index])]
        self.counts[index] += len(chunk)
        if retain:
            self.files[index].write(self.C.pack(retain)); self.files[index].flush()
        self.over |= self.counts[index] > LOG_CAP

    def close(self):
        for f in self.files: f.close()

    def value(self):
        return {k:v for i,name in enumerate(("stdout", "stderr"))
                for k,v in ((name+"_tail_hex", bytes(self.tails[i]).hex()),
                            (name+"_bytes_retained", len(self.tails[i])),
                            (name+"_bytes_seen", self.counts[i]))}


@contextmanager
def capture(directory, C):
    streams = Streams(directory, C); saved = []; threads = []
    def drain(fd, index):
        with os.fdopen(fd, "rb", buffering=0) as source:
            while True:
                chunk = source.read(8192)
                if not chunk: break
                streams.feed(index, chunk)
    try:
        sys.stdout.flush(); sys.stderr.flush()
        for i, fd in enumerate((1, 2)):
            saved.append(os.dup(fd)); r, w = os.pipe()
            os.dup2(w, fd); os.close(w)
            thread = threading.Thread(target=drain, args=(r, i), daemon=True)
            thread.start(); threads.append(thread)
        yield streams
    finally:
        sys.stdout.flush(); sys.stderr.flush()
        for fd, old in zip((1, 2), saved): os.dup2(old, fd); os.close(old)
        for thread in threads: thread.join(timeout=2)
        streams.close()
        C.store(Path(directory)/"6.json", streams.value())


def exitcode(status):
    return -os.WTERMSIG(status) if os.WIFSIGNALED(status) else os.WEXITSTATUS(status)


def cgroup_memory():
    try:
        rel = next(line.split(':', 2)[2] for line in Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0::'))
        base = Path('/sys/fs/cgroup'); root = base/rel.lstrip('/')
        candidates = [root]+[q for q in root.parents if q == base or base in q.parents]
        readings = []
        for directory in candidates:
            if (directory/'memory.current').is_file():
                readings.append({key: (directory/key).read_text().strip() for key in ('memory.current', 'memory.peak', 'memory.events', 'memory.max', 'memory.stat') if (directory/key).is_file()})
        # The nearest finite job allocation is authoritative; node-wide ancestors
        # must not count other users. Fall back to the leaf when no limit is set.
        return next((r for r in readings if r.get('memory.max', 'max') != 'max'), readings[0] if readings else {})
    except (OSError, StopIteration):
        return {}


def mark(C, directory, stage, **extra):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    value = dict(stage=stage, seconds=time.time(), peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024, **extra)
    temp = directory/'5.part'
    C.store(temp, value); temp.replace(directory/'5.json')


def supervise(argv, env, directory, C, end):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    streams = Streams(directory, C); peak = 0; code = None; reason = None; usage = None
    metrics, before = sample_memory()
    process = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    selector = selectors.DefaultSelector()
    for i, stream in enumerate((process.stdout, process.stderr)):
        selector.register(stream, selectors.EVENT_READ, i)
        fcntl.fcntl(stream.fileno(), fcntl.F_SETFL, fcntl.fcntl(stream.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK)
    try:
        while True:
            for key, _ in selector.select(.05):
                chunk = os.read(key.fd, 8192)
                if chunk:
                    streams.feed(key.data, chunk)
                else: selector.unregister(key.fileobj)
            try:
                for line in Path('/proc/%d/status' % process.pid).read_text().splitlines():
                    if line.startswith(('VmHWM:', 'VmRSS:')): peak = max(peak, int(line.split()[1])*1024)
            except OSError: pass
            metrics, memory = sample_memory()
            pid, status, usage = os.wait4(process.pid, os.WNOHANG)
            if pid:
                code = exitcode(status); process.returncode = code
                peak = max(peak, usage.ru_maxrss*1024)
                break
            over = metrics['guarded_bytes'] >= memory_limit(env.get('A_M', 'g'))
            if time.time() >= end or over or streams.over:
                reason = 'memory_budget' if over else 'log_budget' if streams.over else 'deadline'
                try: os.kill(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
    finally:
        # Also reap on a controller alarm/exception; only our own child is affected.
        if process.returncode is None:
            try: os.kill(process.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            pid, status, usage = os.wait4(process.pid, 0)
            code = exitcode(status); process.returncode = code
            peak = max(peak, usage.ru_maxrss*1024)
            reason = reason or 'supervisor_interrupted'
        # Nonblocking bounded drain: inherited pipe handles cannot stall finalization.
        for i, stream in enumerate((process.stdout, process.stderr)):
            for _ in range(128):
                try: chunk = os.read(stream.fileno(), 8192)
                except BlockingIOError: break
                if not chunk: break
                streams.feed(i, chunk)
            stream.close()
        selector.close(); streams.close()
        if streams.over:
            reason = 'log_budget'
            if code == 0: code = 1
        try: stage = C.loads((directory/'5.json').read_bytes())
        except (OSError, ValueError): stage = dict(stage='launch')
        metrics, after = sample_memory()
        value = dict(returncode=code, signal=-code if code is not None and code < 0 else None,
                     signal_name=signal.Signals(-code).name if code is not None and code < 0 else None,
                     peak_rss_bytes=peak, peak_rss_source='wait4_and_proc', last_stage=stage,
                     **streams.value(), **metrics,
                     reason=reason, cgroup_before=before, cgroup_after=after)
        C.store(directory/'6.json', value)
    return code


if __name__ == '__main__':
    p = Path(sys.argv[1]); mode = sys.argv[2]; end = float(sys.argv[3])
    spec = importlib.util.spec_from_file_location('a_storage', p/'9.py')
    C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
    env = dict(os.environ, A_M=mode)
    mark(C, p/'a', 'worker_start')
    code = supervise([sys.executable, '-I', '-s', '-B', str(p/'5.py'), str(p), mode, str(end)], env, p/'a', C, end+1)
    raise SystemExit(0 if code == 0 else 1)
