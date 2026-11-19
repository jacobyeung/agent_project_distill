"""One approved real-model parity process with a node-memory stop threshold.

Run at nice 10 only after the required independent reviews are cleared.
Uses Linux MemAvailable, including reclaimable cache, as free usable RAM.
"""
import json
import os
from pathlib import Path
import runpy
import sys
import threading
import time


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    if os.getpriority(os.PRIO_PROCESS, 0) < 10:
        raise SystemExit('Run this single full-weight check with nice -n 10')
    if '--out' not in sys.argv:
        raise SystemExit('--out is required')
    out = Path(sys.argv[sys.argv.index('--out')+1])
    out.mkdir(parents=True, exist_ok=True)
    threshold = 100_000_000_000
    minimum = [float('inf')]
    stopped = threading.Event()
    started = time.time()
    def available():
        values = {line.split(':')[0]: int(line.split()[1])*1024
                  for line in Path('/proc/meminfo').read_text().splitlines()}
        return values['MemAvailable']
    def receipt(status):
        return dict(status=status, threshold_bytes=threshold,
                    memory_field='MemAvailable (free plus reclaimable cache)',
                    minimum_available_bytes=minimum[0], nice=os.getpriority(os.PRIO_PROCESS, 0),
                    elapsed_seconds=time.time()-started, max_torch_threads=8,
                    approval='inbox/20261110T0646Z_ORCH_answer_real_model_parity.md')
    def check():
        minimum[0] = min(minimum[0], available())
        if minimum[0] < threshold:
            (out/'MEMORY_GUARD.json').write_text(json.dumps(receipt('STOP-MEMORY'), indent=2)+'\n')
            print('STOP-MEMORY: usable node RAM is below 100 GB; no automatic retry', flush=True)
            os._exit(75)
    check()
    def monitor():
        while not stopped.wait(5):
            check()
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    status = 'FAILED'
    try:
        runpy.run_module('tests.ground_backend_real', run_name='__main__')
        status = 'COMPLETED'
    finally:
        stopped.set()
        check()
        (out/'MEMORY_GUARD.json').write_text(json.dumps(receipt(status), indent=2)+'\n')


if __name__ == '__main__':
    main()
