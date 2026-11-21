"""Run one function in a fresh interpreter that copies the caller's process settings."""
import os,pickle,resource,subprocess,sys


def call(module,name,args=(),kwargs=None,*,limit=None):
    """Return module.name(*args,**kwargs) computed in a new interpreter, or raise its exception.

    The new interpreter starts from exec, so it holds no imported module, device handle or driver
    state of the caller. It receives the caller's import path, environment, working directory, umask,
    temporary directory, path scopes and thread count, and the address-space limit `limit`."""
    import tempfile
    from student_pilot import r1_persisted as persisted
    mask=os.umask(0o077);os.umask(mask)
    numeric=sys.modules.get('torch')
    payload=pickle.dumps(dict(path=list(sys.path),tempdir=tempfile.tempdir,umask=mask,
        limit=tuple(resource.getrlimit(resource.RLIMIT_AS) if limit is None else limit),
        threads=numeric.get_num_threads() if numeric is not None else None,
        scope=dict(persisted._paths.get()),proof=persisted._proof.get(),
        module=module,name=name,args=tuple(args),kwargs=dict(kwargs or {})))
    for stream in (sys.stdout,sys.stderr):
        stream.flush()
    source,sink=os.pipe()
    try:
        child=subprocess.Popen([sys.executable,*subprocess._args_from_interpreter_flags(),
                                os.path.abspath(__file__),str(sink)],stdin=subprocess.PIPE,
                               pass_fds=(sink,),env=dict(os.environ),cwd=os.getcwd())
    except BaseException:
        os.close(source);raise
    finally:
        os.close(sink)
    try:
        with os.fdopen(source,'rb') as replies:
            try:
                child.stdin.write(payload)
                child.stdin.close()
            except BrokenPipeError:
                pass
            reply=replies.read()
        status=child.wait()
    finally:
        if child.poll() is None:
            child.kill();child.wait()
    if not reply:
        raise RuntimeError(f'child process exited with status {status} and no result')
    kind,*value=pickle.loads(reply)
    if kind=='value':
        return value[0]
    if kind=='error':
        raise value[0]
    raise _rebuild(*value)


def _rebuild(module,name,message):
    import importlib
    try:
        kind=importlib.import_module(module)
        for part in name.split('.'):
            kind=getattr(kind,part)
        error=kind(message)
        if isinstance(error,BaseException) and str(error)==message:
            return error
    except Exception:
        pass
    return RuntimeError(f'{module}.{name}: {message}')


def _encode(reply):
    try:
        data=pickle.dumps(reply);pickle.loads(data)
        return data
    except Exception:
        error=reply[1] if reply[0]=='error' else TypeError('result is not picklable: '+type(reply[1]).__name__)
    try:
        data=pickle.dumps(('error',error));pickle.loads(data)
        return data
    except Exception:
        return pickle.dumps(('text',type(error).__module__,type(error).__qualname__,str(error)))


def _apply(payload):
    sys.path[:]=payload['path']
    resource.setrlimit(resource.RLIMIT_AS,(payload['limit'][0],resource.getrlimit(resource.RLIMIT_AS)[1]))
    os.umask(payload['umask'])
    import tempfile
    tempfile.tempdir=payload['tempdir']
    if payload['threads'] is not None:
        import torch
        torch.set_num_threads(payload['threads'])
    import importlib
    from contextlib import ExitStack
    from student_pilot.r1_persisted import scope,proof_scope
    with ExitStack() as stack:
        if payload['proof']:
            stack.enter_context(proof_scope())
        stack.enter_context(scope(payload['scope']))
        function=getattr(importlib.import_module(payload['module']),payload['name'])
        return function(*payload['args'],**payload['kwargs'])


def serve(sink):
    """Child side: read the call from stdin, write the pickled reply to file descriptor `sink`."""
    try:
        import ctypes,signal
        ctypes.CDLL(None).prctl(1,signal.SIGKILL)
    except Exception:
        pass
    with os.fdopen(sink,'wb') as replies:
        try:
            reply=('value',_apply(pickle.load(sys.stdin.buffer)))
        except BaseException as error:
            import traceback
            traceback.print_exc()
            reply=('error',error)
        replies.write(_encode(reply))


if __name__=='__main__':
    serve(int(sys.argv[1]))
