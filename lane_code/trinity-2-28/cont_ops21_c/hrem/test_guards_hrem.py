"""Offline follow-up checks; synthetic receipts are not Orchard CPU evidence."""
import ast
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
RAM = HERE/'validation'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())


def dump(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def unpack(archive, root):
    with tarfile.open(str(archive)) as t:
        for m in t:
            assert m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts
            p = root / m.name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(t.extractfile(m).read())


def main():
    assert sys.version_info[:2] == (3, 6)
    work = Path(tempfile.mkdtemp(prefix='followup_', dir=str(RAM)))
    parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);args=parser.parse_args()
    report = read(Path(args.build))['H']
    p = work / 'package'
    unpack(Path(report['delivery_dir']) / '1.tgz', p)
    results = p / 'a/c'
    results.mkdir()
    public = read(p / '0.json')
    operator = runpy.run_path(str(p / 'a/6.py'))
    # The fixture represents a completed fill; it cannot be used to submit.
    dump(p/'a/1.json',dict(types=['camera_displacement', 'camera_rotation', 'camera_movement_direction']))
    root = work / 'synthetic_cpu_root'
    requested = ['namespace', '/python', '-B', '-I', str(root / 'a/5.py'), str(root / 'a/1.json')]
    with tarfile.open(str(p / '0.tgz')) as t:
        guard_sha = hashlib.sha256(t.extractfile('orchard_h10/vendor/return_io.py').read()).hexdigest()
    guard = dict(passed=True, operator_sha256=sha(p / 'a/6.py'),
        operator_sha256_before=sha(p / 'a/6.py'), operator_sha256_after=sha(p / 'a/6.py'),
        write_test=dict(bytes=4 * 1024**2, sha256=hashlib.sha256(b'fixture').hexdigest()),
        pool=str(root / 'wpool'), token=public['token'], guard_target_sha256=guard_sha,
        batch_sha256=sha(p / 'BATCH.sh'), path='7.py', guard_target='6.py', action='test',
        events=['guard_installed', 'write_test', 'operator_dispatch'], requested_argv=requested,
        dispatched_argv=requested[:-2] + [str(root / '7.py'), str(root / 'a/1.json')])
    memory = operator['memory_bound']()
    # Evaluate the exact CPU.json construction used by a/5.py after a/6.py's rehearsal.
    cpu_tree = ast.parse((p / 'a/5.py').read_text())
    write = next(n for n in ast.walk(cpu_tree) if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name) and n.func.id == 'write'
        and isinstance(n.args[0], ast.BinOp)
        and isinstance(n.args[0].right, ast.Str) and n.args[0].right.s == 'CPU.json')
    fixture = eval(compile(ast.Expression(write.args[1]), '<actual CPU.json construction>', 'eval'),
        dict(entry_sequence=dict(guard, entry_sequence_passed=True), bundle_guard=guard,
             memory=memory, cfg=public, sha=sha, package=p,
             sequence=p / 'a/6.py', proof={'synthetic': True}, ready={'synthetic': True}, root=root))
    script = (HERE / 'sub_guard_hrem.sh').read_text()
    checker = script.split("<<'PYCODE'\n", 1)[1].split('\nPYCODE', 1)[0]
    pool_checker = script.split("<<'PYCODE'\n")[2].split('\nPYCODE', 1)[0]

    def check(value):
        dump(results / 'CPU.json', value)
        dump(results / 'MEMORY.json', value['memory'])
        return subprocess.run(['/usr/bin/python3', '-I', '-s', '-B', '-', str(p)],
            input=checker.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    good = check(fixture)
    assert good.returncode == 0, good.stderr.decode()
    mutations = {
        'passed': (['passed'], False),
        'bundle_passed': (['bundle_guard_passed'], False),
        'entry_passed': (['entry_sequence_passed'], False),
        'payload': (['payload'], '0' * 64),
        'plan': (['plan'], '0' * 64),
        'operator': (['operator_sha256'], '0' * 64),
        'inputs': (['inputs'], '0' * 64),
        'batch': (['bundle_guard', 'batch_sha256'], '0' * 64),
        'events': (['entry_sequence', 'events'], ['operator_dispatch', 'write_test', 'guard_installed']),
        'guard_target': (['entry_sequence', 'guard_target_sha256'], '0' * 64),
        'write_bytes': (['entry_sequence', 'write_test', 'bytes'], 1),
        'write_sha': (['entry_sequence', 'write_test', 'sha256'], 'invalid'),
        'argv': (['entry_sequence', 'requested_argv'], []),
        'memory_fit': (['memory', 'fits'], False),
        'memory_captures': (['memory', 'reads', 0, 'captures'], 134),
    }
    for name, (keys, value) in mutations.items():
        bad = copy.deepcopy(fixture)
        target = bad
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value
        assert check(bad).returncode != 0, name
    assert check(fixture).returncode == 0
    pool = work / 'pool'
    pool.mkdir()
    pool_code = pool_checker.replace("root='/project/community/jjyeung/okh7/ae71c903'", 'root=' + repr(str(pool)))
    def pool_run(code):
        return subprocess.run(['/usr/bin/python3', '-I', '-s', '-B', '-'], input=code.encode(),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
    assert pool_run(pool_code) == 0
    # Model large stat results without creating large files.
    (pool / 'one').write_text('x')
    large = pool_code.replace('total+=os.stat(p).st_size', 'total+=75000001')
    assert pool_run(large) != 0
    (pool / 'link').symlink_to(pool / 'one')
    assert pool_run(pool_code) != 0
    missing = pool_code.replace(repr(str(pool)), repr(str(work / 'absent')))
    assert pool_run(missing) != 0
    for name in ('o_cpu_hrem.sh', 'o_sub_hrem.sh', 'o_build_hrem.sh', 'o_place_fill_hrem.sh', 'o_fetch_hrem.sh'):
        subprocess.run(['bash', '-n', str(HERE / name)], check=True)
    assert 'trap_test' not in (HERE / 'cpu_guard_hrem.sh').read_text() + script
    assert 'squeue -u jjyeung -p general -h' in script
    assert 'test ! -s "$P/a/9.txt"' in script
    result = dict(passed=True, python=sys.version.split()[0], synthetic_receipt_only=True,
        receipt_writer='H a/5.py CPU.json expression',
        receipt_negative_cases=sorted(mutations),
        pool_checks=['empty passes', 'over 75 MB rejected', 'symlink rejected', 'missing rejected'],
        bash_syntax_scripts=['o_cpu_hrem.sh', 'o_sub_hrem.sh', 'o_build_hrem.sh', 'o_place_fill_hrem.sh', 'o_fetch_hrem.sh'],
        empty_general_guard_retained=True,
        orchard_submitted=False, work=str(work))
    dump(work / 'FOLLOWUP_RESULTS.json', result)
    dump(HERE / 'GUARD_TEST_RESULTS.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
