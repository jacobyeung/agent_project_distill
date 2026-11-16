"""Portable namespace rehearsal. All writes stay in the extracted package."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import job_support as H

def main():
    root = Path(__file__).resolve().parent
    out = root / 'out'
    out.mkdir(exist_ok=True)
    result = dict(namespace_executed=False, full_job_rehearsal=False)
    try:
        assert Path.cwd() == root
        S, R, NS, J = H.native()
        package = json.loads((root / 'packet/PACKAGE.json').read_text())
        archive = root / 'packet/d6e92a81.tar'
        assert archive.stat().st_size == package['source_bytes'] and H.sha(archive) == package['source']
        stage = out / ('stage_' + uuid.uuid4().hex[:8])
        H.unpack(S, archive, stage)
        for name in ('fsw', 'm/ap', 'project', 'cache', 'temp', 'home', 'sj/a7e31d84'):
            (stage / name).mkdir(parents=True, exist_ok=True)
        shutil.copyfile('/usr/bin/bwrap', stage / 'bwrap')
        (stage / 'bwrap').chmod(0o700)
        argv = NS.namespace(stage, dict(logical_run='/scratch/jjyeung/a7e31d84'))
        runtimes = [('runtime/p1cpu', '/scratch/jjyeung/envs/p1cpu'),
                    ('runtime/uv', '/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu')]
        for packed, logical in runtimes:
            local = root / packed
            if not local.exists():
                # Local pre-bwrap probe can use the installed read-only runtime.
                # The remote archive builder requires both packed runtime trees.
                local = Path(logical)
                result['runtime_not_packed'] = True
            assert local.is_dir(), 'The CPU interpreter must be included for the remote node'
            argv += ['--ro-bind', str(local), logical]
        argv += ['--bind', str(root), str(root), '--unshare-net', '--chdir', str(root),
                 '/scratch/jjyeung/envs/p1cpu/bin/python', '-B', str(root / 'rehearse_v2.py')]
        H.dump(out / 'ARGV.json', argv)
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                   OPENBLAS_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1',
                   HOME=str(stage / 'home'), XDG_CACHE_HOME=str(stage / 'cache'),
                   HF_HOME=str(stage / 'cache/a'), TORCH_HOME=str(stage / 'cache/b'),
                   TMPDIR=str(stage / 'temp'), A_META=str(root / 'inputs/a.tar'))
        with (out / 'namespace.log').open('w') as log:
            process = subprocess.run(argv, env=env, cwd=root, stdout=log, stderr=subprocess.STDOUT)
        result.update(returncode=process.returncode, namespace_executed=process.returncode == 0)
    except Exception as error:
        result['error'] = dict(type=type(error).__name__, message=str(error))
    finally:
        H.dump(out / 'RESULT.json', result)
        with tarfile.open(out / 'RH_RESULT.tar', 'w') as archive:
            for base in (out, root / 'evidence'):
                paths = base.iterdir() if base == out else base.rglob('*')
                for path in sorted(paths) if base.exists() else []:
                    if path.is_file() and not path.is_symlink() and path.name != 'RH_RESULT.tar':
                        archive.add(path, arcname=str(path.relative_to(root)), recursive=False)
        H.dump(out / 'RH_RESULT.pin.json', dict(bytes=(out / 'RH_RESULT.tar').stat().st_size,
                                               sha256=H.sha(out / 'RH_RESULT.tar')))
    print(json.dumps(result))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
