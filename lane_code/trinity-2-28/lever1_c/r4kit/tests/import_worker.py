"""Fresh-process import audit, launched through runpy with the staged Python."""
import sys

# -S prevents ambient .pth files; only the staged stdlib and admitted site tree
# can supply dependencies. No host stdlib path survives this assignment.
stdlib, site, package, output, native_site = sys.argv[1:]
sys.path[:] = [stdlib, stdlib+'/lib-dynload', site, native_site]
import importlib.util
import json
from pathlib import Path
import runpy
import time
import torch
# The local torchvision Python modules are real. Its unused CUDA NMS operator
# needs only a schema for import with this host's CPU torch build.
vision_fixture = torch.library.Library('torchvision', 'DEF')
vision_fixture.define('nms(Tensor dets, Tensor scores, float iou_threshold) -> Tensor')

p = Path(package)
spec = importlib.util.spec_from_file_location('a_storage', p/'9.py')
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
C.install(p, outputs=[p/'d/e'])

runtime = runpy.run_path(str(p/'5.py'), run_name='a_runtime')
runtime['run'].__globals__['C'] = C
closure = runtime['import_closure'](p)
assert 'student_pilot.carrier_c1_canary' in closure['required_modules']
from parity_kit import stage_restore
class ImportsComplete(Exception): pass
def stop_before_inputs(*args, **kwargs): raise ImportsComplete()
stage_restore.stage = stop_before_inputs
try:
    runtime['run'](p, 'c', time.time()+60)
except ImportsComplete:
    pass
else:
    raise AssertionError('Worker did not reach restore after real imports')
finally:
    import signal
    signal.setitimer(signal.ITIMER_REAL, 0)
    state = runtime['run'].__globals__
    if state['WATCH_STOP'] is not None: state['WATCH_STOP'].set()
    if state['WATCH_THREAD'] is not None: state['WATCH_THREAD'].join(timeout=1)

origins = {name: str(getattr(module, '__file__', '') or '') for name, module in sys.modules.items()}
for name, origin in origins.items():
    if origin == __file__: continue  # Includes multiprocessing's __mp_main__ alias.
    if (name, origin) in (('torch.ops', '_ops.py'), ('torch.classes', '_classes.py')):
        continue  # PyTorch's synthetic namespace objects, not file-backed modules.
    if origin and not origin.startswith(('<', stdlib+'/', site+'/', native_site+'/', str(p)+'/')):
        raise AssertionError((name, origin))
Path(output).write_text(json.dumps(dict(passed=True, imports=closure['required_modules'],
    modules=origins, closure=closure, reached='restore', stdlib=stdlib, site=site), indent=2)+'\n')
