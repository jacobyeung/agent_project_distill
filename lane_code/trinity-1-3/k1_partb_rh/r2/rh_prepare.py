"""Portable namespace rehearsal. All writes stay in the extracted package."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tarfile
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import job_support as H

def refusal(log, nested):
    text = log.lower()
    if 'namespace' in text and any(s in text for s in
            ('not permitted', 'permission', 'disabled', 'not enabled', 'no space left')):
        return 'nested_user_namespace_refused' if nested else 'outer_namespace_refused'
    return 'inner_namespace_or_rehearsal_failed' if nested else 'outer_bwrap_failed'

def collect(root, code):
    """Return diagnostics even if bwrap could not launch the preparation process."""
    out = root / 'out'
    result = dict(namespace_executed=False, full_job_rehearsal=False,
                  outer_namespace_started=False, evidence_runs=[])
    record = out / 'RESULT.json'
    if record.exists():
        result.update(json.loads(record.read_text()))
    result['outer_returncode'] = code
    if not result['outer_namespace_started']:
        with (out / 'outer.log').open() as log:
            result['diagnostic'] = log.read(65536)
        result['reason'] = refusal(result['diagnostic'], nested=False)
    H.dump(record, result)
    with tarfile.open(out / 'RH_RESULT.tar', 'w') as archive:
        for path in sorted(out.iterdir()):
            if path.is_file() and not path.is_symlink() and path.name not in ('RH_RESULT.tar', 'RH_RESULT.pin.json'):
                archive.add(path, arcname=str(path.relative_to(root)), recursive=False)
        for name in result['evidence_runs']:
            assert Path(name).name == name and name.startswith('v2_')
            for path in sorted((root / 'evidence' / name).rglob('*')):
                if path.is_file() and not path.is_symlink():
                    archive.add(path, arcname=str(path.relative_to(root)), recursive=False)
        latest = root / 'evidence/V2_LATEST.json'
        if result['evidence_runs'] and latest.is_file():
            if Path(json.loads(latest.read_text())['run']).name in result['evidence_runs']:
                archive.add(latest, arcname='evidence/V2_LATEST.json', recursive=False)
    H.dump(out / 'RH_RESULT.pin.json', dict(bytes=(out / 'RH_RESULT.tar').stat().st_size,
                                           sha256=H.sha(out / 'RH_RESULT.tar')))
    print(json.dumps(result))
    return 0

def main():
    root = Path(__file__).resolve().parent
    out = root / 'out'
    out.mkdir(exist_ok=True)
    result = dict(namespace_executed=False, full_job_rehearsal=False,
                  outer_namespace_started=True, evidence_runs=[])
    before = set((root / 'evidence').glob('v2_*'))
    try:
        assert Path.cwd() == root
        assert root.is_relative_to('/tmp'), 'Preparation requires the private /tmp namespace'
        S, R, NS, J = H.native()
        package = json.loads((root / 'packet/PACKAGE.json').read_text())
        archive = root / 'packet/d6e92a81.tar'
        assert archive.stat().st_size == package['source_bytes'] and H.sha(archive) == package['source']
        stage = Path('/tmp') / ('a_' + uuid.uuid4().hex[:12])
        result['stage'] = str(stage)
        H.unpack(S, archive, stage)
        for name in ('fsw', 'm/ap', 'project', 'cache', 'temp', 'home', 'sj/a7e31d84'):
            (stage / name).mkdir(parents=True, exist_ok=True)
        shutil.copyfile('/usr/bin/bwrap', stage / 'bwrap')
        (stage / 'bwrap').chmod(0o700)
        logical_run = '/scratch/jjyeung/a7e31d84'
        argv = NS.namespace(stage, dict(logical_run=logical_run))
        runtimes = [('runtime/p1cpu', '/scratch/jjyeung/envs/p1cpu'),
                    ('runtime/uv', '/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu')]
        for packed, logical in runtimes:
            # Bind targets must exist before sj becomes read-only.
            (stage / 'sj' / Path(logical).relative_to('/scratch/jjyeung')).mkdir(parents=True, exist_ok=True)
            local = root / packed
            if not local.exists():
                # Local pre-bwrap probe can use the installed read-only runtime.
                # The remote archive builder requires both packed runtime trees.
                local = Path(logical)
                result['runtime_not_packed'] = True
            assert local.is_dir(), 'The CPU interpreter must be included for the remote node'
            argv += ['--ro-bind', str(local), logical]
        # The unchanged phase requires output under /scratch. This alias writes
        # into the package's evidence directory; stage/cache/home remain in /tmp.
        argv += ['--bind', str(root), str(root), '--bind', str(root), logical_run,
                 '--unshare-net', '--chdir', logical_run,
                 '/scratch/jjyeung/envs/p1cpu/bin/python', '-I', '-s', '-B',
                 logical_run + '/rh_prepare.py', '--inside']
        H.dump(out / 'ARGV.json', argv)
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                   OPENBLAS_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1',
                   HOME=str(stage / 'home'), XDG_CACHE_HOME=str(stage / 'cache'),
                   HF_HOME=str(stage / 'cache/hf'), TORCH_HOME=str(stage / 'cache/torch'),
                   TRITON_CACHE_DIR=str(stage / 'cache/triton'),
                   TMPDIR=str(stage / 'temp'), TMP=str(stage / 'temp'), TEMP=str(stage / 'temp'),
                   HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                   A_META=str(root / 'inputs/a.tar'), A_MODEL=str(root / 'inputs/model.tar'))
        with (out / 'namespace.log').open('w') as log:
            process = subprocess.run(argv, env=env, cwd=root, stdout=log, stderr=subprocess.STDOUT)
        result.update(returncode=process.returncode,
                      namespace_executed=(out / 'NAMESPACE_ENTERED.json').is_file())
        if process.returncode:
            with (out / 'namespace.log').open() as log:
                result['diagnostic'] = log.read(65536)
            result['reason'] = ('rehearsal_failed' if result['namespace_executed'] else
                                refusal(result['diagnostic'], nested=True))
    except Exception as error:
        result['error'] = dict(type=type(error).__name__, message=str(error))
    finally:
        result['evidence_runs'] = sorted(p.name for p in set((root / 'evidence').glob('v2_*')) - before if p.is_dir())
        result['coverage_files'] = ['evidence/' + name + '/COVERAGE.json' for name in result['evidence_runs']
                                    if (root / 'evidence' / name / 'COVERAGE.json').is_file()]
        H.dump(out / 'RESULT.json', result)
    print(json.dumps(result))
    return 0 if result.get('returncode') == 0 else 1

if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    if sys.argv[1:2] == ['--collect']:
        raise SystemExit(collect(root, int(sys.argv[2])))
    if sys.argv[1:] == ['--inside']:
        H.dump(root / 'out/NAMESPACE_ENTERED.json', dict(host=socket.gethostname(), root=str(root),
               home=os.environ['HOME'], temp=os.environ['TMPDIR'], cache=os.environ['XDG_CACHE_HOME']))
        os.execv(sys.executable, [sys.executable, '-B', str(root / 'rehearse_v2.py')])
    raise SystemExit(main())
