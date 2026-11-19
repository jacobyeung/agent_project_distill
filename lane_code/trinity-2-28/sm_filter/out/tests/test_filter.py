"""Run with python3 -I -s -B; all fixtures stay below workspace/work/tmp_*."""
import gzip
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from unittest import mock

PACKAGE = Path(__file__).resolve().parents[1]
WORK = PACKAGE.parent / 'work'
FILTER = PACKAGE / 'tools/lane_code_filter.py'


def put(root, relative, data=None):
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data if data is not None else relative.encode('utf8'))


def walk_order(paths):
    # Independent traversal oracle: files at each directory precede sorted child dirs.
    def visit(prefix):
        tails = [p[len(prefix):] for p in paths if p.startswith(prefix)]
        result = [prefix + x for x in sorted(t for t in tails if '/' not in t)]
        for name in sorted(set(t.split('/')[0] for t in tails if '/' in t)):
            result += visit(prefix + name + '/')
        return result
    return visit('')


def run(root, robust, label='trinity-2-28', manifest=None):
    # Exercise the production stdin protocol, including -I -s -B.
    command = [sys.executable, '-I', '-s', '-B', '-', label]
    if manifest:
        command.append(manifest)
    env = dict(os.environ, LCS_ROBUST_SYNC=str(robust), CUDA_VISIBLE_DEVICES='')
    result = subprocess.run(command, input=FILTER.read_bytes(), cwd=str(root), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
    assert result.returncode == 0, result.stderr.decode('utf8', 'replace')
    return result


def main():
    WORK.mkdir(exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix='tmp_filter_', dir=str(WORK)))
    keep = ['00_first.py', 'lane/REPORT.md', 'lane/reviews/review.md', 'lane/receipts/pin.json',
            'lane/prompts/job.md', 'lane/config/run.yaml', 'lane/work/build24f/build.py',
            'lane/work/build24f/REPORT.md', 'lane/work/build24f/kits/own.py',
            'lane/work/build24f/tests/test_source.py', 'lane/work/build24f/review_tests.py',
            'lane/work/build24f/integration.py', 'lane/work/builder_source.py',
            'lane/work/tree/source.py', 'lane/work/prompts/prompt.md',
            'lane/payload/README.md', 'lane/environment/config.yaml', 'lane/vendor/source.py',
            'lane/work/base/module.py', 'lane/tree/module.py', 'lane/src/extract/source.py',
            'lane/work/build24f/resolver/resolve.py', 'lane/sequence_native/source.py',
            'lane/review_tests/test_source.py', 'lane/integration/test_source.py',
            'lane/work/shop_abcdefgh/source.py', 'lane/work/shop_12345678/source.py',
            'lane/work/shop_________/source.py', 'lane/work/shop_abcd123/source.py',
            'lane/work/shop_abcde1234/source.py', 'lane/work/shop_abcd1234x/source.py',
            'lane/work/shop_ABCD1234/source.py', 'lane/work/prefix_' + 'a' * 31 + '/source.py',
            'lane/work/h' + 'a' * 31 + '/source.py', 'lane/orch_n30_notes/notes.md',
            'lane/scratch/other/source.py', 'lane/work/build24f/workbench/source.py',
            'lane/test_runs_notes/source.py', 'lane/tests/test_runs.py',
            'lane/source space/unicode_é.yaml', 'lane/new\tline/name\nfile.md',
            'lane/work/shop_abcd1234\n/source.py', 'lane/work/test_runs\n/source.py',
            'lane/src/module_' + 'a1' * 16 + '.py', 'lane/config_abcd1234.json',
            'tmp_lane/source.py', 'test_runs/source.py', 'driver_a2sjw8b2/source.py',
            '0123456789abcdef0123456789abcdef/source.py']
    for name in ('out', 'out_round1', 'out_round42', 'in', 'kit', 'kits', 'src', 'tests', 'code', 'inputs'):
        keep.append('lane/' + name + '/own.py')
    exclude_dirs = ['test_runs', 'TEST_RUNS', 'test-artifacts', 'TEST-ARTIFACTS',
                    'LANE_TEST_OUTPUT', 'lane_test_output', 'B2_TEST_OUTPUT', 'b2_test_output',
                    'TMPDIR', 'tmpdir', 'R2_PROOFS', 'r2_proofs',
                    'finetune_gate_test_typ_3nah', 'provisional_zl3iszux', 'driver_a2sjw8b2',
                    'sam_r10_ljgx_vjf', 'sam_r10_abcdefgh', 'provisional_abcdefgh',
                    'driver_abcdefgh', 'finetune_gate_test_abcdefgh',
                    'direction_prior_' + 'a1' * 16, 'fix3_b_arms_' + 'b2' * 16,
                    'prefix_' + 'A1' * 16 + '_suffix', 'a' * 32, '7' * 32, 'f' * 40,
                    'job_abcd1234', 'job_1_______a', 'job_a______1', 'job_1______a',
                    'job_a1______', 'line\nbreak_' + 'a1' * 16, 'a1' * 16 + '\nend',
                    'line\nbreak_abcd1234', 'patch_validation_one', 'PATCH_VALIDATION_ONE',
                    'fixtry', 'FIXTRY', 'sandbox', 'SANDBOX', 'sandboxes', 'SANDBOXES',
                    'rehearsal', 'rehearsal3', 'REHEARSAL4', 'attic', 'ATTIC',
                    '.cache', 'download_cache', '__pycache__', 'node_modules', '.git',
                    'site-packages', 'conda-meta', 'env', '.venv', 'tmp_output', 'results',
                    'test_products', 'artifacts', 'frames_out']
    # This suffix has nine chars, so it is deliberately retained.
    exclude_dirs.remove('job_1_______a')
    keep.append('lane/work/job_1_______a/source.py')
    excluded = ['lane/work/' + name + '/source.py' for name in exclude_dirs]
    excluded += ['lane/payload/environment/lib/python3.12/module.py',
                 'lane/payload/environment/lib/itcl4.2.3/config.sh',
                 'lane/payload/environment/conda-meta/pkg.json',
                 'lane/payload/lib/python3.12/module.py',
                 'lane/fb_pack/ro/orch_n30/other_lane/out/report.md',
                 'lane/payload/files/scratch/jjyeung/other/code.py',
                 'lane/so_in/scratch/jjyeung/orch_n30/other/source.py',
                 'lane/work/extract/src/source.py', 'lane/w24/attic/kit/own.py',
                 'lane/work/build24f/rehearsal3/kit/own.py',
                 'lane/work/build24f/work/prompts/generated.md',
                 'lane/work/build24f/review_tests/before/kit/BUILD.json',
                 'lane/work/build24f/integration2/kit/BUILD.json',
                 'lane/out/test_runs/generated.py', 'lane/tests/test-artifacts/generated.py',
                 'lane/work/prompts/TMPDIR/generated.py', 'lane/work/tree/sandbox/generated.py',
                 'lane/work/devin_traces/file.txt', 'lane/src/site-packages-copy.py']
    # devin_traces is only excluded below out, not below arbitrary work.
    excluded.remove('lane/work/devin_traces/file.txt')
    excluded.append('lane/out/devin_traces/file.txt')
    for path in keep + excluded:
        put(root, path)
    put(root, 'lane/duplicates/duplicate.py', (root / '00_first.py').read_bytes())
    put(root, 'lane/ignored.bin')
    put(root, 'lane/large.py', b'x' * (512 * 1024 + 1))
    put(root, 'lane/large.json', b'y' * (256 * 1024 + 1))
    os.mkfifo(str(root / 'lane/fifo.py'))
    os.symlink('REPORT.md', str(root / 'lane/link.py'))
    os.symlink('src', str(root / 'lane/linked_directory'))
    os.symlink('missing', str(root / 'lane/broken.py'))
    # MAXDIR must still apply to ordinary dirs, but not to source tests or root lanes.
    for directory, should_keep in [('crowded_lane', True), ('lane/tests', True), ('lane/crowded', False)]:
        for i in range(2001):
            put(root, directory + '/entry%04d.bin' % i, b'')
        path = directory + '/keep.py'
        put(root, path)
        if should_keep:
            keep.append(path)
    expected = b''.join(p.encode('utf8') + b'\0' for p in walk_order(keep))
    outputs = []
    for robust in (0, 1):
        result = run(root, robust)
        assert result.stdout == expected, ('mode', robust,
            'extra', set(result.stdout.split(b'\0')) - set(expected.split(b'\0')),
            'missing', set(expected.split(b'\0')) - set(result.stdout.split(b'\0')))
        assert b'skipped_bigdirs=1' in result.stderr, result.stderr
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1]
    print('PASS exact NUL output: both paths, %d kept files, %d excluded path cases; FIFO and symlinks skipped' % (len(keep), len(excluded)))
    print('PASS MAXDIR: ordinary directory excluded; top-level lane and tests preserved')
    manifests = []
    dup_content = b'lane/duplicates/duplicate.py\t00_first.py\n'
    for robust in (0, 1):
        mdir = 'manifests%s' % robust
        first = run(root, robust, 'trinity-1-1', mdir)
        one = (root / mdir / 'DEDUP_trinity-1-1.tsv.gz').read_bytes()
        time.sleep(1.05)
        second = run(root, robust, 'trinity-1-1', mdir)
        two = (root / mdir / 'DEDUP_trinity-1-1.tsv.gz').read_bytes()
        run(root, robust, 'trinity-1-2', mdir + '_other')
        three = (root / (mdir + '_other') / 'DEDUP_trinity-1-2.tsv.gz').read_bytes()
        assert one == two == three
        assert first.stdout == second.stdout == expected + (mdir + '/DEDUP_trinity-1-1.tsv.gz').encode() + b'\0'
        assert one[4:8] == b'\0' * 4 and not (one[3] & 8), 'mtime/FNAME header'
        assert gzip.decompress(one) == dup_content
        manifests.append(one)
    assert manifests[0] == manifests[1]
    print('PASS deterministic manifests: repeat runs, different labels/directories, both paths; mtime=0, no FNAME')
    spec = importlib.util.spec_from_file_location('dry_count', str(PACKAGE / 'tools/dry_count.py'))
    dry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dry)
    boundary = Path('/scratch/jjyeung/orch_n30')
    for review in ('0', '1'):
        with mock.patch.dict(os.environ, LCS_REVIEW2_FIXES=review):
            with mock.patch.object(dry.os, 'listdir', return_value=[]):
                for relative in keep:
                    if '/' not in relative:
                        continue
                    assert dry.root_gate(FILTER, boundary / str(Path(relative).parent)) is None, relative
                for relative in excluded:
                    # Filename substring rules are not directory root gates.
                    if relative.endswith('site-packages-copy.py'):
                        continue
                    assert dry.root_gate(FILTER, boundary / str(Path(relative).parent)), relative
            with mock.patch.object(dry.os, 'listdir', return_value=['x'] * 2001):
                for relative in ('tmp_lane', 'lane', 'lane/tests', 'lane/out_round4', 'lane/work/prompts'):
                    # work itself must have <=MAXDIR when checking its protected child.
                    with mock.patch.object(dry.os, 'listdir', side_effect=lambda p: [] if p.name == 'work' else ['x'] * 2001):
                        assert dry.root_gate(FILTER, boundary / relative) is None, relative
                assert dry.root_gate(FILTER, boundary / 'lane/crowded')
    print('PASS dry_count root gate: every fixture directory rule, ancestor gates and protected/MAXDIR rules in both review modes')
    # Changes to dry_count must stay within its AST reader and root gate.
    original = (PACKAGE.parent / 'in/tools/dry_count.py').read_text()
    new = (PACKAGE / 'tools/dry_count.py').read_text()
    assert original[original.index('\ndef main():'):] == new[new.index('\ndef main():'):]
    source = FILTER.read_text()
    assert 'LCS_FILTER_EOF' not in source and 'PYEOF' not in source
    for tool in (FILTER, PACKAGE / 'tools/dry_count.py'):
        compile(tool.read_bytes(), str(tool), 'exec')
    print('PASS stdin delimiters, syntax and unchanged dry_count main')
    print('ALL FILTER TESTS PASSED on Python ' + sys.version.split()[0])


if __name__ == '__main__':
    main()
