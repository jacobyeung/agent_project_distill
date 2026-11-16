"""Run the pinned k6 builder wa.py unchanged as a governed stream.
Every HTTP range body is also written to fd 1, which feeds ratelimit.py, so pipe backpressure bounds the fetch rate;
an own average cap (RATE bytes/s, as wa_rl.py) applies too. Stops itself before any network IO. No exec, no children.
usage: wa_gov.py RATE WA_PY PLAN.json STORE_DIR STORE_PREFIX OUT.jsonl 1
"""
import hashlib, importlib.util, os, signal, sys, threading, time
rate, wa_path = float(sys.argv[1]), sys.argv[2]
if hashlib.sha256(open(wa_path, 'rb').read()).hexdigest() != 'e31661181dfb829d0ae22866d49975996176294dcd54c8d7c7e5584dbb342a33':
    raise SystemExit('wa.py differs from the k6 RECEIPT pin')
if sys.argv[-1] != '1':
    raise SystemExit('run with THREADS=1')
data_out = sys.__stdout__.buffer
sys.stdout = sys.stderr
spec = importlib.util.spec_from_file_location('wa', wa_path); wa = importlib.util.module_from_spec(spec); spec.loader.exec_module(wa)
os.kill(os.getpid(), signal.SIGSTOP)
raw, lock, state = wa.get_range, threading.Lock(), {'bytes': 0, 't0': time.monotonic()}
def governed(url, a, b):
    data = raw(url, a, b)
    with lock:
        data_out.write(data); data_out.flush()
        state['bytes'] += len(data)
        wait = state['bytes'] / rate - (time.monotonic() - state['t0'])
    if wait > 0:
        time.sleep(wait)
    return data
wa.get_range = governed
sys.argv = [wa_path] + sys.argv[3:]
wa.main()
print('GOVERNED_TOTAL', state['bytes'], round(time.monotonic() - state['t0'], 1), flush=True)
