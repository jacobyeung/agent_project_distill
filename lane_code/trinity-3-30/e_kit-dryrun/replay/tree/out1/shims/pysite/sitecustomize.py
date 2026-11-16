"""Starts the dry-run line tracer in child interpreters that read PYTHONPATH.

dryrun.py copies this file into OUTDIR/shims/pysite/ and bakes in TRACE_PY. It then runs the
environment's own sitecustomize, if one exists further down sys.path, so the kit sees no change.
"""
import os
import sys

TRACE_PY = '/scratch/jjyeung/orch_n30/e_kit-dryrun/replay/tree/out1/shims/trace.py'


def _start():
    try:
        if 'orchkit_dryrun_trace' in sys.modules:
            return
        import importlib.util
        spec = importlib.util.spec_from_file_location('orchkit_dryrun_trace', TRACE_PY)
        module = importlib.util.module_from_spec(spec)
        sys.modules['orchkit_dryrun_trace'] = module
        spec.loader.exec_module(module)
        module.start()
    except Exception:
        pass


def _chain():
    here = os.path.dirname(os.path.abspath(__file__))
    for entry in sys.path:
        if not entry or os.path.abspath(entry) == here:
            continue
        candidate = os.path.join(entry, 'sitecustomize.py')
        if os.path.isfile(candidate):
            try:
                with open(candidate, 'rb') as handle:
                    exec(compile(handle.read(), candidate, 'exec'), {'__name__': 'sitecustomize',
                                                                       '__file__': candidate})
            except Exception:
                pass
            return


_start()
_chain()
