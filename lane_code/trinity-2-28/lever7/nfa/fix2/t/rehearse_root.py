"""Run a CPU-check entry (a/5.py) through the job's own launcher line, locally, up to its first
namespace launch: root creation, bootstrap extraction, the installed process guard, and the bundle
guard's write test (the guarded Popen that killed job 174294). Only what needs Orchard is stubbed:
input checks against /project, export pins, the job_tmp mount proof, staging copies. The first
checked_run (the namespace launch) is scanned by the real opaque() and then stopped.
Run inside `unshare -r -m` with /tmp bound to a lane folder.
argv: <5.py> <package dir> <results dir> <mode: new|old_tripped|exists>"""
import importlib.abc
import importlib.machinery
import json
import os
import runpy
import sys
import traceback
from pathlib import Path

entry, package, results, mode = sys.argv[1:5]
LOG = []


def post(name, module):
    if name == 'orchard_h10.job':
        module.check_inputs = lambda raw, cfg, package=None: raw
        def stage(root, cfg, inputs, S, J):  # staging copies need /project; keep its root/a
            (Path(root)/'a').mkdir()
            LOG.append(['stage_stub', str(root)])
            return {}
        module.stage = stage
    elif name == 'orchard_h10.export_pins':
        module.load = lambda inputs, package: {}
    elif name == 'orchard_job':
        module.storage_proof = lambda path, mountinfo=None, job=None: dict(stub=True, path=str(path), job=job)
    elif name == 'orchard_h10.common':
        real = module.checked_run

        def checked_run(argv, **kwargs):
            module.opaque(argv)  # the real guard on the real argv
            if kwargs.get('env'):
                module.opaque([f'{k}={v}' for k, v in kwargs['env'].items()])
            LOG.append(['checked_run', list(map(str, argv)), sorted(kwargs.get('env', {}).items())])
            raise SystemExit('REHEARSAL_STOP first namespace launch reached')
        module.checked_run = checked_run
    elif name == 'orchard_results':
        real_po = module.pool_operation

        def pool_operation(action, pool, token, local=None, timeout=60):
            LOG.append(['pool_operation', action, str(pool), token])
            return real_po(action, pool, token, local=local, timeout=timeout)
        module.pool_operation = pool_operation


class Hook(importlib.abc.MetaPathFinder):
    names = {'orchard_h10.job', 'orchard_h10.export_pins', 'orchard_job', 'orchard_h10.common', 'orchard_results'}

    def find_spec(self, name, path, target=None):
        if name not in self.names:
            return None
        spec = importlib.machinery.PathFinder.find_spec(name, path)
        if spec is None:
            return None
        loader = spec.loader
        exec_module = loader.exec_module

        def wrapped(module):
            exec_module(module)
            post(name, module)
            LOG.append(['imported', name, getattr(module, '__file__', '')])
        loader.exec_module = wrapped
        return spec


sys.meta_path.insert(0, Hook())
if mode == 'old_tripped':
    import tempfile
    tempfile._RandomNameSequence.__next__ = lambda self: '5wh1sx88'  # 174294's generated suffix
if mode == 'exists':
    job = os.environ['SLURM_JOB_ID']
    Path('/tmp/a%s-%d' % (job, os.getpid())).mkdir(mode=0o700)
# Real Popen spawn of the guarded write test must use this interpreter, as the job's does.
sys.argv = [entry, '--package', package, '--sequence', package + '/a/6.py', '--results', results,
            '--seconds', '10800']
out = dict(mode=mode, job=os.environ['SLURM_JOB_ID'], pid=os.getpid())
try:
    runpy.run_path(entry, run_name='__main__')
    out['end'] = 'returned'
except SystemExit as e:
    out['end'] = str(e)
except BaseException as e:
    out['end'] = 'raised'
    out['error'] = '%s: %s' % (type(e).__name__, e)
    out['traceback'] = traceback.format_exc()
roots = sorted(str(p) for p in Path('/tmp').glob('a%s*' % os.environ['SLURM_JOB_ID']))
out['roots'] = roots
for r in roots:
    p = Path(r)
    out.setdefault('root_modes', {})[r] = oct(p.stat().st_mode & 0o777)
    out.setdefault('root_has', {})[r] = sorted(x.name for x in p.iterdir())
out['log'] = LOG
print(json.dumps(out, indent=1))
