"""fix21 dp.py tests: run the kit's b/dp.py (runpy, its own argv) with os.statvfs patched to a chosen free byte count.
Usage: tdp.py <free bytes or 'real'> <dp.py args...>; prints dp.py's line and the exit code."""
import os, runpy, sys, types
free = sys.argv[1]; script = sys.argv[2]
if free != 'real':
    os.statvfs = lambda p, _f=int(free): types.SimpleNamespace(f_bavail=_f, f_frsize=1)
sys.argv = [script] + sys.argv[3:]
try:
    runpy.run_path(script, run_name='__main__'); code = 0
except SystemExit as e:
    code = e.code
print('EXIT', code)
