"""Incremental capture memory receipts, including unfinished captures."""
from collections import deque
from pathlib import Path
import os
import resource
import threading
import time


class Monitor:
    def __init__(self, meta, torch):
        self.meta=Path(meta);self.torch=torch;self.rows=[];self.lines=deque(maxlen=200)
        self.current=None;self.lock=threading.RLock();self.done=threading.Event()
        self.thread=threading.Thread(target=self.loop,daemon=True)
        self.thread.start()

    def begin(self, capture):
        with self.lock:
            self.torch.cuda.reset_peak_memory_stats()
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
            gpu_max_allocated_bytes=self.torch.cuda.max_memory_allocated())
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
