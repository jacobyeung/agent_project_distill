"""Line tracer for a dry run, limited to the kit's own files. Standard library only; Python 3.6-safe.

dryrun.py copies this file into OUTDIR/shims/trace.py and bakes in the constants below. It runs in
three ways:
  * as the entry's wrapper: `python [flags] trace.py -- script.py args` (also `-- -m mod`, `-- -c code`);
  * from OUTDIR/shims/pysite/sitecustomize.py, for child interpreters that read PYTHONPATH;
  * inside every traced process, subprocess.Popen rewrites a child python command line so the child
    runs under this wrapper too (this reaches children started with -I, which ignore PYTHONPATH).

Each process writes TRACE_DIR/trace_<pid>_<token>.json with, per traced file, its sha256, the lines
that ran and the lines that can run (the line starts of every code object, as rh_coverage.py
computed them). Python 3.8+ also logs opens and listings of hidden roots to hidden_<pid>.jsonl and every
directory creation to mkdir_<pid>.jsonl (the dry run flags one directory created by two processes).
A tracer failure never changes what the kit does: every tracer error is swallowed.
"""
import atexit
import dis
import hashlib
import json
import os
import sys
import threading
import types

TRACE_DIR = ''  # baked by dryrun.py
ROOTS = []  # baked by dryrun.py: directory prefixes whose .py files are the kit's own
HIDDEN = []  # baked by dryrun.py: roots a dry run hides (/home, /data*, ...)
TRACE_PY = ''  # baked by dryrun.py: this file's path

_state = {'started': False, 'lines': {}, 'cache': {}, 'token': None, 'in_hook': False}


def _under(name, roots):
    for root in roots:
        if name == root or name.startswith(root.rstrip('/') + '/'):
            return True
    return False


def _mine(name):
    cache = _state['cache']
    hit = cache.get(name)
    if hit is None:
        hit = name.endswith('.py') and _under(os.path.abspath(name), ROOTS)
        cache[name] = hit
    return hit


def _local(frame, event, arg):
    if event == 'line':
        _state['lines'].setdefault(frame.f_code.co_filename, set()).add(frame.f_lineno)
    return _local


def _global(frame, event, arg):
    if not _mine(frame.f_code.co_filename):
        return None
    if event == 'call':
        _state['lines'].setdefault(frame.f_code.co_filename, set())
    return _local


def statements(code):
    """Executable line numbers of a code object and every nested code object."""
    lines = set()
    for item in dis.findlinestarts(code):
        line = item[1]
        if line is not None and line > 0:
            lines.add(line)
    for child in code.co_consts:
        if isinstance(child, types.CodeType):
            lines |= statements(child)
    return lines


def save():
    try:
        files = {}
        for name, lines in list(_state['lines'].items()):
            try:
                with open(name, 'rb') as handle:
                    raw = handle.read()
                possible = statements(compile(raw, name, 'exec'))
            except Exception:
                continue
            files[os.path.abspath(name)] = {'sha256': hashlib.sha256(raw).hexdigest(),
                                            'executed': sorted(set(lines) & possible),
                                            'possible': sorted(possible)}
        modules = sorted(set(os.path.abspath(m.__file__) for m in list(sys.modules.values())
                             if getattr(m, '__file__', None) and _mine(m.__file__)))
        row = {'pid': os.getpid(), 'python': sys.executable, 'argv': sys.argv[:8],
               'files': files, 'modules': modules}
        if _state['token'] is None:
            _state['token'] = os.urandom(4).hex() if hasattr(bytes, 'hex') else '0'
        target = os.path.join(TRACE_DIR, 'trace_%d_%s.json' % (os.getpid(), _state['token']))
        tmp = target + '.tmp'
        with open(tmp, 'w') as handle:
            handle.write(json.dumps(row, sort_keys=True))
        os.rename(tmp, target)
    except Exception:
        pass


def _fs_log(name, row):
    _state['in_hook'] = True
    try:
        with open(os.path.join(TRACE_DIR, '%s_%d.jsonl' % (name, os.getpid())), 'a') as handle:
            handle.write(json.dumps(row) + '\n')
    except Exception:
        pass
    finally:
        _state['in_hook'] = False


def _hidden_hook(event, args):
    if _state['in_hook'] or event not in ('open', 'os.listdir', 'os.scandir', 'os.mkdir', 'os.chdir',
                                          'os.rename', 'shutil.copyfile', 'os.symlink', 'os.link'):
        return
    try:
        for value in args[:2]:
            if isinstance(value, bytes):
                value = value.decode('utf-8', 'replace')
            if not isinstance(value, str) or not value.startswith('/'):
                continue
            if _under(os.path.normpath(value), HIDDEN):
                _fs_log('hidden', {'event': event, 'path': value})
                return
        if event == 'os.mkdir' and isinstance(args[0], (str, bytes)) and len(args) > 2 and args[2] in (None, -1):
            target = args[0].decode('utf-8', 'replace') if isinstance(args[0], bytes) else args[0]
            _fs_log('mkdir', {'path': os.path.abspath(target), 'argv': sys.argv[:3]})
    except Exception:
        pass


def rewrite(argv):
    """Insert this tracer in front of the script of a python command line; else return argv."""
    try:
        argv = list(argv)
        for i, token in enumerate(argv):
            base = os.path.basename(str(token))
            if not (base.startswith('python') and base[6:].replace('.', '').isdigit() or base == 'python'
                    or str(token) == sys.executable):
                continue
            j = i + 1
            while j < len(argv):
                flag = str(argv[j])
                if flag in ('-c', '-m') or not flag.startswith('-') or flag == '-':
                    break
                if flag.startswith('--'):
                    return argv
                if flag in ('-W', '-X', '-Q'):
                    j += 2
                    continue
                if 'c' in flag[1:] or 'm' in flag[1:]:
                    return argv
                j += 1
            if j >= len(argv) or str(argv[j]) in (TRACE_PY, '-'):
                return argv
            return argv[:j] + [TRACE_PY, '--'] + argv[j:]
        return argv
    except Exception:
        return argv


def _patch_popen():
    import subprocess
    original = subprocess.Popen.__init__
    if getattr(original, '_orchkit_dryrun', False):
        return

    def init(self, args, *rest, **kwargs):
        if isinstance(args, (list, tuple)):
            args = rewrite(args)
        return original(self, args, *rest, **kwargs)
    init._orchkit_dryrun = True
    subprocess.Popen.__init__ = init


def _patch_exit():
    real = os._exit
    if getattr(real, '_orchkit_dryrun', False):
        return

    def _exit(code):
        save()
        real(code)
    _exit._orchkit_dryrun = True
    os._exit = _exit


def start():
    if _state['started']:
        return
    _state['started'] = True
    try:
        _patch_popen()
        _patch_exit()
        atexit.register(save)
        if hasattr(sys, 'addaudithook') and HIDDEN:
            sys.addaudithook(_hidden_hook)
        if hasattr(os, 'register_at_fork'):
            os.register_at_fork(after_in_child=lambda: _state.update(token=None))
    except Exception:
        pass
    threading.settrace(_global)
    sys.settrace(_global)


def run_target(args):
    """Run `script args`, `-m mod args` or `-c code args` as python itself would."""
    if not args:
        sys.stderr.write('trace.py: nothing to run\n')
        return 2
    if args[0] == '-c':
        sys.argv = ['-c'] + args[2:]
        main = types.ModuleType('__main__')
        main.__dict__['__builtins__'] = __builtins__
        sys.modules['__main__'] = main
        if not sys.flags.isolated and sys.path and sys.path[0] == os.path.dirname(TRACE_PY):
            sys.path[0] = ''
        exec(compile(args[1], '<string>', 'exec'), main.__dict__)
        return 0
    if args[0] == '-m':
        import runpy
        sys.argv = [args[1]] + args[2:]
        if not sys.flags.isolated and sys.path and sys.path[0] == os.path.dirname(TRACE_PY):
            sys.path[0] = os.getcwd()
        runpy.run_module(args[1], run_name='__main__', alter_sys=True)
        return 0
    script = args[0]
    sys.argv = list(args)
    if not sys.flags.isolated and sys.path and sys.path[0] == os.path.dirname(TRACE_PY):
        sys.path[0] = os.path.dirname(os.path.realpath(script))
    main = types.ModuleType('__main__')
    main.__dict__.update(__file__=script if sys.version_info < (3, 9) else os.path.abspath(script),
                         __builtins__=__builtins__, __cached__=None)
    sys.modules['__main__'] = main
    with open(script, 'rb') as handle:
        code = compile(handle.read(), script, 'exec')
    exec(code, main.__dict__)
    return 0


def main_entry():
    args = sys.argv[1:]
    if args and args[0] == '--':
        args = args[1:]
    shared = sys.modules.get('orchkit_dryrun_trace')
    if shared is not None and shared._state['started']:
        shared_mod = shared
    else:
        sys.modules['orchkit_dryrun_trace'] = sys.modules[__name__]
        shared_mod = sys.modules[__name__]
        start()
    try:
        return run_target(args)
    finally:
        shared_mod.save()


if __name__ == '__main__':
    sys.exit(main_entry())
