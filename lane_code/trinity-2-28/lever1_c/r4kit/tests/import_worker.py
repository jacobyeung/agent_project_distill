"""Fresh-process import audit, launched through runpy with the staged Python."""
import sys

# -S prevents ambient .pth files; only the staged stdlib and admitted site tree
# can supply dependencies. No host stdlib path survives this assignment.
stdlib, site, package, output = sys.argv[1:]
sys.path[:] = [stdlib, stdlib+'/lib-dynload', site]
import ast
import importlib.util
import json
from pathlib import Path
import runpy
import time

p = Path(package)
spec = importlib.util.spec_from_file_location('a_storage', p/'9.py')
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
C.install(p, outputs=[p/'d/e'])

# Audit every syntactic import, including imports inside CPU/GPU functions.
# Executing from-import statements also forces their requested attributes and
# lazily loaded package submodules, rather than merely importing the root.
imports = set()
for name in ('5.py', '7.py', '9.py', '10.py', '11.py'):
    wrapper = ast.parse((p/name).read_text()).body[0].value
    source = bytes.fromhex(ast.literal_eval(wrapper.args[0].args[0].args[0]))
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            statement = ast.unparse(node)
            exec(compile(ast.Module(body=[node], type_ignores=[]), name, 'exec'), {})
            imports.add(statement)

# Explicitly exercise lazy stdlib dependencies used by launch, archives,
# diagnostics and native model libraries; importtime records their closure.
for name in ('keyword', 'pkgutil', 'collections', 'asyncio', 'concurrent.futures',
             'multiprocessing', 'email', 'email.policy', 'xml.dom.minidom',
             'email._encoded_words', 'importlib.readers', 'importlib.resources.readers',
             'xml.sax.expatreader', 'xml.sax.xmlreader',
             'xmlrpc.client', 'wave', 'pydoc', 'unittest', 'venv', 'ensurepip'):
    __import__(name)

runtime = runpy.run_path(str(p/'5.py'), run_name='a_runtime')
closure = runtime['import_closure'](p)
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
    if origin and not origin.startswith(('<', stdlib+'/', site+'/', str(p)+'/')):
        raise AssertionError((name, origin))
Path(output).write_text(json.dumps(dict(passed=True, imports=sorted(imports),
    modules=origins, closure=closure, reached='restore', stdlib=stdlib, site=site), indent=2)+'\n')
