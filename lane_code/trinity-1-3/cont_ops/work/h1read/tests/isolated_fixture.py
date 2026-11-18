"""Isolated CPU children with exact-command admission and fixture-only writes."""
import base64
import io
import json
import os
from pathlib import Path
import re
import runpy
import shlex
import subprocess
import sys
import tarfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
_POPEN = subprocess.Popen


def package(root):
    import orchard_launcher as L
    config = L.prepare('a000000001', root/'prepared', 544, run='469ddece',
                       generation='mstop', families=['a7'])
    script = (root/'prepared/BATCH.sh').read_text()
    raw = base64.b64decode(re.search(r"raw=base64.b64decode\('([^']+)'", script)[1])
    def extract(raw):
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            for member in archive:
                path = root/member.name
                assert member.isfile() and path.resolve().is_relative_to(root.resolve())
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.extractfile(member).read())
    extract(raw)
    extract((root/'bootstrap/payload.tar.gz').read_bytes())
    payload = root/'sj'/Path(config['spec']['package']).relative_to('/scratch/jjyeung')
    wrapper = payload/'vllm_isolated.sh'
    production = '#!/bin/sh\nexec '+shlex.quote(str(L.J.AP/'19252904/e/bin/python'))+' -I "$@"\n'
    assert wrapper.read_text() == production
    # Only the interpreter location differs from the generated production wrapper.
    wrapper.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' -I "$@"\n')
    wrapper.chmod(0o700)
    return payload


def launch(root, wrapper, mode, target, *args, popen=False, **kwargs):
    import offline_guard
    root, wrapper = Path(root).resolve(), Path(wrapper).resolve()
    assert root.is_relative_to(ROOT/'evidence') and root.relative_to(ROOT/'evidence').parts[0].startswith('test_')
    assert wrapper.is_relative_to(root)
    assert Path(target).resolve().is_relative_to(root)
    assert wrapper.read_text() == '#!/bin/sh\nexec '+shlex.quote(sys.executable)+' -I "$@"\n'
    assert mode in ('import', 'help', 'runtime', 'chain', 'chain_worker')
    command = [str(wrapper), '-B', str(Path(__file__).resolve()), str(root), mode, str(target), *map(str, args)]
    with offline_guard.local_fixture_command(command):
        if popen:
            return _POPEN(command, cwd=root, **kwargs)
        return subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=120, **kwargs)


def main():
    root, mode, target, *args = sys.argv[1:]
    root, target = Path(root).resolve(), Path(target).resolve()
    assert sys.flags.isolated and sys.flags.dont_write_bytecode
    assert root.is_relative_to(ROOT/'evidence') and root.relative_to(ROOT/'evidence').parts[0].startswith('test_')
    assert target.is_relative_to(root)
    sys.path.insert(0, str(ROOT/'tests'))
    import offline_guard
    def writes(event, values):
        if event in ('os.remove', 'os.rmdir'):
            raise RuntimeError('Deletion forbidden')
        paths = []
        if event == 'open' and not isinstance(values[0], int):
            if values[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                paths = values[:1]
        elif event in ('os.mkdir', 'os.chmod'):
            paths = values[:1]
        elif event in ('os.rename', 'os.link', 'os.symlink'):
            paths = values[:2]
        for value in paths:
            if not Path(value).absolute().is_relative_to(root) or not Path(value).resolve().is_relative_to(root):
                raise RuntimeError('Write outside fixture: '+str(value))
    sys.addaudithook(writes)
    assert str(target.parent) not in sys.path
    sys.argv = [str(target), *args]
    if mode == 'import':
        runpy.run_path(str(target), run_name='isolated_import')
    elif mode == 'help':
        sys.argv = [str(target), '--help']
        runpy.run_path(str(target), run_name='__main__')
    elif mode == 'runtime':
        os.environ['A_FIXTURE_ROOT'] = str(root)
        os.environ['A_FIXTURE_WORKER'] = str(target)
        # Cold import before mocks or runtime paths can mask an entry-point failure.
        sys.argv = [str(target), '--help']
        try:
            runpy.run_path(str(target), run_name='__main__')
        except SystemExit as error:
            assert error.code == 0
        os.environ['FIX4_DIRECT'] = args[0]
        runpy.run_path(str(ROOT/'tests/runtime_fixture.py'), run_name='__main__')
    elif mode == 'chain':
        config = json.loads(Path(args[1]).read_text())
        os.environ['A_JOB_CONFIG'] = args[1]
        wrapper = config['spec']['interpreters']['vllm']
        def child(command, **kwargs):
            assert command[:3] == [wrapper, '-B', str(target.with_name('worker.py'))]
            return launch(root, wrapper, 'chain_worker', command[2], *command[3:], popen=True, **kwargs)
        with patch.object(subprocess, 'Popen', child):
            # launch() keeps the real Popen for guarded local children.
            runpy.run_path(str(target), run_name='__main__')
    elif mode == 'chain_worker':
        runpy.run_path(str(target), run_name='isolated_worker')
        config = json.loads(Path(args[1]).read_text())
        family = args[3]
        print('private engine diagnostic', flush=True)
        if family == config.get('fixture_failure'):
            raise SystemExit(7)
        dest = Path(config['spec']['run'])/family
        dest.mkdir()
        (dest/'COMPLETE.json').write_text(json.dumps(dict(items=1, isolated=sys.flags.isolated)))
        (dest/'ITEMS.jsonl').write_text(json.dumps(dict(id=family, family=family, task_type='t', score=1))+'\n')
    else:
        raise ValueError(mode)


if __name__ == '__main__':
    main()
