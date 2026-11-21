"""Incremental capture memory receipts, including unfinished captures."""
from collections import deque
from pathlib import Path
import os
import resource
import threading
import time


class Monitor:
    def __init__(self, meta, torch, cuda=True):
        # The CPU check runs this monitor without CUDA; GPU calls stay unchanged.
        self.meta=Path(meta);self.torch=torch;self.cuda=cuda;self.rows=[];self.lines=deque(maxlen=200)
        self.current=None;self.lock=threading.RLock();self.done=threading.Event()
        self.thread=threading.Thread(target=self.loop,daemon=True)
        self.thread.start()

    def begin(self, capture):
        with self.lock:
            if self.cuda:self.torch.cuda.reset_peak_memory_stats()
            self.started=time.monotonic()
            self.current=dict(capture=capture,status='active',phase='0',rss_peak_bytes=0)
            self.rows.append(self.current)
            self.snapshot()

    def phase(self, value):
        with self.lock:
            self.current['phase']=value;self.snapshot()

    def snapshot(self):
        from orchard_h10.common import write
        from orchard_h10.e import save
        if self.current is None:return
        rss=0
        for line in Path('/proc/self/status').read_text().splitlines():
            if line.startswith('VmRSS:'):rss=int(line.split()[1])*1024
        self.current.update(seconds=time.monotonic()-self.started,
            rss_peak_bytes=max(rss,self.current['rss_peak_bytes']),
            process_rss_hwm_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            gpu_max_allocated_bytes=self.torch.cuda.max_memory_allocated() if self.cuda else 0)
        write(self.meta/'15.json',self.rows)
        os.replace(self.meta/'15.json',self.meta/'5.json')
        # Hex storage keeps capture identities and diagnostic names private.
        import j
        self.lines.append(j.wire_dumps(self.current,sort_keys=True))
        save(self.meta/'16.json',self.lines)
        os.replace(self.meta/'16.json',self.meta/'13.json')

    def finish(self, status):
        with self.lock:
            self.current['status']=status;self.snapshot()
            row=dict(self.current);self.current=None
            return row

    def loop(self):
        while not self.done.wait(1):
            with self.lock:self.snapshot()

    def close(self):
        self.done.set();self.thread.join(timeout=2)
        if self.current is not None:self.finish('incomplete')


def tree_rss(pid, proc=Path('/proc')):
    """Current RSS summed over a process and its descendants."""
    pending=[pid];seen=set();total=0
    while pending:
        pid=pending.pop()
        if pid in seen:continue
        seen.add(pid)
        try:
            for line in (proc/str(pid)/'status').read_text().splitlines():
                if line.startswith('VmRSS:'):total+=int(line.split()[1])*1024
            for task in (proc/str(pid)/'task').iterdir():
                try:pending.extend(map(int,(task/'children').read_text().split()))
                except OSError:pass
        except OSError:pass
    return total


def cgroup_memory(base=Path('/sys/fs/cgroup'), cgroup=Path('/proc/self/cgroup')):
    """The nearest cgroup v2 level with a finite memory.max (the job allocation)."""
    try:
        rel=next(line.split(':',2)[2] for line in cgroup.read_text().splitlines() if line.startswith('0::'))
        root=base/rel.lstrip('/')
        readings=[]
        for directory in [root]+[q for q in root.parents if q==base or base in q.parents]:
            if (directory/'memory.current').is_file():
                readings.append({k:(directory/k).read_text().strip() for k in
                    ('memory.current','memory.peak','memory.max','memory.stat') if (directory/k).is_file()})
        return next((r for r in readings if r.get('memory.max','max')!='max'),readings[0] if readings else {})
    except (OSError,StopIteration):
        return {}


def guarded_memory(values, resident):
    """Cgroup charge minus reclaimable file pages (staged archives sit in page cache)."""
    try:
        stat=dict(line.split() for line in values['memory.stat'].splitlines())
        reclaimable=int(stat['active_file'])+int(stat['inactive_file'])
        if 'file' in stat and 'shmem' in stat:
            reclaimable=min(reclaimable,max(0,int(stat['file'])-int(stat['shmem'])))
        return max(0,int(values['memory.current'])-reclaimable),'cgroup'
    except (KeyError,ValueError,TypeError):
        return resident,'process_tree_rss'


class Guard:
    """Sample the CPU unit's memory once a second; stop it before the cgroup limit."""
    def __init__(self, pid, limit, on_over, sample=None, interval=1.):
        self.pid=pid;self.limit=limit;self.on_over=on_over;self.interval=interval
        self.sample=sample or (lambda:(cgroup_memory(),tree_rss(self.pid)))
        self.peaks=dict(guarded_bytes=0,tree_rss_bytes=0,cgroup_current_bytes=None,cgroup_peak_bytes=None)
        self.source=None;self.over=False;self.cgroup_max=None
        self.done=threading.Event();self.thread=threading.Thread(target=self.loop,daemon=True)
    def check(self):
        values,resident=self.sample()
        guarded,self.source=guarded_memory(values,resident)
        self.cgroup_max=values.get('memory.max',self.cgroup_max)
        for key,value in (('guarded_bytes',guarded),('tree_rss_bytes',resident)):
            self.peaks[key]=max(self.peaks[key],value)
        for key,name in (('cgroup_current_bytes','memory.current'),('cgroup_peak_bytes','memory.peak')):
            try:self.peaks[key]=max(self.peaks[key] or 0,int(values[name]))
            except (KeyError,ValueError):pass
        if guarded>=self.limit and not self.over:
            self.over=True;self.on_over()
        return guarded
    def loop(self):
        while not self.done.wait(self.interval):
            try:self.check()
            except Exception:pass
    def __enter__(self):
        self.check();self.thread.start();return self
    def __exit__(self,*args):
        self.done.set();self.thread.join(timeout=2)
    def receipt(self):
        return dict(limit_bytes=self.limit,source=self.source,over=self.over,cgroup_max=self.cgroup_max,**self.peaks)
