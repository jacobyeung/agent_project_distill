from . import _record, _fail, _os

_record('import', module=__name__, pid=_os.getpid())
_fail(__name__)
