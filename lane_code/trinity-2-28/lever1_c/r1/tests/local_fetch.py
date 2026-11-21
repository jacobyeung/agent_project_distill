"""Run unchanged production fetch code with only the pool filesystem relocated."""
import json
import pathlib
import runpy
import subprocess
import sys

mode, package, pool, local_pool, job, script = sys.argv[1:]
OriginalPath = pathlib.PosixPath
shared=OriginalPath('/project/community/jjyeung')/json.loads((OriginalPath(package)/'0.json').read_text())['token']


class LocalPath(pathlib.PosixPath):
    def __new__(cls, *parts):
        return object.__new__(cls)

    def __init__(self, *parts):
        path = OriginalPath(*parts)
        if path == OriginalPath(pool) or OriginalPath(pool) in path.parents:
            path = OriginalPath(local_pool) / path.relative_to(pool)
        if path==shared or shared in path.parents:path=OriginalPath(package)/path.relative_to(shared)
        super().__init__(path)


pathlib.Path = LocalPath
if mode == 'child':
    sys.argv = [str(LocalPath(package)/'3.py'), 'fetch', '--return-token',
                job, '--out', str(LocalPath(package)/'a/f')]
    runpy.run_path(sys.argv[0], run_name='__main__')
else:
    import tempfile
    original_temp=tempfile.mkdtemp
    tempfile.mkdtemp=lambda **kw:original_temp(dir=OriginalPath(package).parent,**kw)
    original_run = subprocess.run

    def local_child(argv, **kwargs):
        # The production fetch launches its numeric entry in another interpreter.
        # Preserve the program and arguments and install the same filesystem map.
        assert argv[:4] == ['/usr/bin/python3', '-I', '-s', '-B']
        assert argv[4:7] == [str(LocalPath(package)/'3.py'), 'fetch', '--return-token']
        assert argv[8:] == ['--out', str(LocalPath(package)/'a/f')]
        return original_run([sys.executable, '-I', '-s', '-B', __file__, 'child',
                             package, pool, local_pool, argv[7], script], **kwargs)

    subprocess.run = local_child
    code = OriginalPath(script).read_text().split("<<'PY'\n", 1)[1].split('\nPY\n', 1)[0]
    sys.argv = ['-', package, job]
    exec(compile(code, script + ':production-python', 'exec'), {'__name__': '__main__'})
