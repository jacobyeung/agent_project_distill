"""Import-only llguidance overlay; every attempted guidance operation fails."""
import json as _json
import os as _os

_MSG = 'llguidance stub: guidance structured outputs are unavailable on this host (glibc 2.28)'


def _record(event, **fields):
    path = _os.environ.get('LLG_STUB_LOG') or _os.path.join(_os.environ.get('TMPDIR', '/tmp'), 'llg_stub_calls.jsonl')
    data = (_json.dumps(dict(event=event, **fields), sort_keys=True) + '\n').encode()
    fd = _os.open(path, _os.O_WRONLY | _os.O_CREAT | _os.O_APPEND, 0o600)
    try:
        if _os.write(fd, data) != len(data):
            raise RuntimeError('llguidance stub: incomplete audit write')
    finally:
        _os.close(fd)


def _fail(name):
    _record('call', name=name)
    raise RuntimeError(_MSG + ' (' + name + ')')


_record('import', module=__name__, pid=_os.getpid())


class _UnavailableMeta(type):
    def __getattr__(cls, name):
        _fail(cls.__name__ + '.' + name)


class _Unavailable(metaclass=_UnavailableMeta):
    def __init__(self, *args, **kwargs):
        _fail(type(self).__name__)


class LLMatcher(_Unavailable):
    pass


class LLTokenizer(_Unavailable):
    pass


class LLInterpreter(_Unavailable):
    pass


def __getattr__(name):
    _fail('llguidance.' + name)
