"""Local link/pull guards; sparse fixtures and test-only pins, Python 3.6 stdlib."""
import difflib
import hashlib
import json
import os
import py_compile
import re
import subprocess
import sys
import uuid
from pathlib import Path

H = Path(__file__).resolve().parent
W = H/'rehearsal/link'
RUN = W/('run_'+uuid.uuid4().hex)
RUN.mkdir()
os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
NAMES = ['o_%s_c600.sh' % n for n in ('build', 'place_pull_fill', 'cpu', 'sub', 'fetch')]
NAME = NAMES[1]
before = (W/'before'/NAME).read_text()
after = (H/NAME).read_text()
start = before.index('for i in 0 1 2 3; do\n')
end = before.index('\nfor X in A; do\n', start)
new_start = after.index('MODE=$( '.replace('$', '\\$'))
new_end = after.index('\nfor X in A; do\n', new_start)
assert before[:start] == after[:new_start]
assert before[end:] == after[new_end:]
pull = before[start:end]
assert after[new_start:new_end].count(pull) == 1
diff = []
for name in NAMES:
    old, new = (W/'before'/name).read_bytes(), (H/name).read_bytes()
    if name != NAME:
        assert old == new, name
    diff.extend(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True),
                                     'before/'+name, 'after/'+name))
    subprocess.run(['bash', '-n', str(H/name)], check=True)
(W/'DIFF.txt').write_text(''.join(diff))

# The current reviewed scripts constrain this fix to the embedded reuse helper.
fix_before = W/'fix2/before'
fix_diff = []
for name in NAMES:
    old, new = (fix_before/name).read_text(), (H/name).read_text()
    if name == NAME:
        prefix, rest = old.split("<<'REUSE_PY'\n", 1)
        suffix = rest.split('\nREUSE_PY', 1)[1]
        assert new.split("<<'REUSE_PY'\n", 1)[0] == prefix
        assert new.split('\nREUSE_PY', 1)[1] == suffix
    else:
        assert old == new, name
    fix_diff.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                       'before/'+name, 'after/'+name))
(W/'fix2/DIFF.txt').write_text(''.join(fix_diff))
generated = RUN/'generated'
subprocess.run([sys.executable, '-B', str(H/'gen600c.py'), str(generated)],
               stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
for name in NAMES:
    assert (generated/name).read_bytes() == (H/name).read_bytes(), name

# Render the actual unquoted outer heredoc, without placement or nohup execution.
embedded = after.split('<<SHELLCODE\n', 1)[1].split('\nSHELLCODE', 1)[0]
render = 'S=/fixture/stage; PA=/fixture/package\ncat <<SHELLCODE\n' + embedded + '\nSHELLCODE\n'
full = subprocess.run(['bash'], input=render.encode(), stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE, check=True).stdout.decode()
(RUN/'fill.sh').write_text(full)
subprocess.run(['bash', '-n', str(RUN/'fill.sh')], check=True)
block = full[full.index('MODE=$( '):full.index('\nfor X in A; do\n')]
production_python = block.split("<<'REUSE_PY'\n", 1)[1].split('\nREUSE_PY', 1)[0]
(RUN/'reuse.py').write_text(production_python)
for path in (H/'gen600c.py', H/'test_link_c600.py', RUN/'reuse.py'):
    py_compile.compile(str(path), cfile=str(RUN/(path.name+'.py36c')), doraise=True)
assert sys.version_info[:3] == (3, 6, 8), sys.version
pin_line = next(line for line in production_python.splitlines() if line.startswith('pin = '))
production_pin = json.loads((H/'in/BIND600.json').read_text())
assert str(production_pin['archive_bytes']) in pin_line
assert production_pin['archive_sha256'] in pin_line
assert production_pin['archive_bytes'] // 4 == 5395758080

SIZE = 256 * 1024
seed = RUN/'seed'; seed.mkdir()
digest = hashlib.sha256()
for i in range(4):
    path = seed/str(i)
    with path.open('wb') as stream:
        stream.write(('sparse part %d' % i).encode())
        stream.seek(SIZE-1)
        stream.write(bytes([i+1]))
    assert path.stat().st_blocks * 512 < SIZE
    digest.update(path.read_bytes())
tiny = dict(object=production_pin['object'], archive_bytes=4*SIZE,
            archive_sha256=digest.hexdigest())
(RUN/'TEST_ONLY_BIND600.json').write_text(json.dumps(tiny, sort_keys=True)+'\n')
tiny = json.loads((RUN/'TEST_ONLY_BIND600.json').read_text())
marker = '%s %s %s\n' % (tiny['object'], tiny['archive_bytes'], tiny['archive_sha256'])

bin_dir = RUN/'bin'; bin_dir.mkdir()
# gsutil is a local recorder: it cannot contact a service.
stub = '''#!/usr/bin/python3
import json, os, sys
from pathlib import Path
with open(os.environ['PULL_LOG'], 'a') as stream:
    stream.write(json.dumps(sys.argv[1:])+'\\n')
index = int(sys.argv[-2].rsplit('.part0', 1)[1][0])
if os.environ.get('FAIL_PULL') == str(index):
    sys.exit(23)
Path(sys.argv[-1]).write_bytes((Path(os.environ['SEED'])/str(index)).read_bytes())
'''
(bin_dir/'gsutil').write_text(stub); (bin_dir/'gsutil').chmod(0o700)
results = []
logs = []


def record(label):
    results.append(label)
    logs.append('PASS: '+label)
    print(logs[-1])


def fixture(label):
    root = RUN/label/'KROOT'; root.mkdir(parents=True)
    return root


def source(root, name='a15_cot_ap100', defect=None, independent=False):
    src = root/name/'a/e'; src.mkdir(parents=True)
    (src/'5').write_text('wrong marker\n' if defect == 'marker' else marker)
    for i in range(4):
        dest = src/str(i)
        if i == 3 and defect == 'missing':
            continue
        if i == 3 and defect == 'symlink':
            dest.symlink_to(seed/str(i)); continue
        if i == 3 and defect == 'directory':
            dest.mkdir(); continue
        if i == 3 and defect in ('size', 'sha'):
            with dest.open('wb') as stream:
                stream.write(b'bad')
                stream.seek(SIZE if defect == 'size' else SIZE-1)
                stream.write(b'!')
        elif independent:
            dest.write_bytes((seed/str(i)).read_bytes())
        else:
            os.link(str(seed/str(i)), str(dest))
    return src


def execute(root, reuse=None, search=False, failed_link=False, fail_pull=None,
            mutation=None):
    dest = root/'a15_cot_ap000_destination/a/e'; dest.mkdir(parents=True)
    # Placement has already copied this marker; discovery must skip this package.
    (dest/'5').write_text(marker)
    code = block.replace(pin_line, 'pin = '+repr(tiny))
    code = code.replace('/project/community/jjyeung/okh7', str(root))
    if failed_link:
        inject = '''
real_link = os.link
def fail_third(src, dst, **kwargs):
    if Path(dst).name == '2':
        raise OSError('Synthetic link failure after two successful links')
    return real_link(src, dst, **kwargs)
os.link = fail_third
'''
        code = code.replace('dest = Path(sys.argv[1])', inject+'\ndest = Path(sys.argv[1])')
    if mutation:
        inject = '''
mutation = %r
real_link = os.link
def change(part):
    part = Path(part)
    if mutation[0] == 'replace':
        part.rename(str(part)+'.original')
        # Identical content still must not pass an inode-identity check.
        part.write_bytes(Path(str(part)+'.original').read_bytes())
    elif mutation[0] == 'symlink':
        part.rename(str(part)+'.original')
        part.symlink_to(str(part)+'.original')
    else:
        saved = part.stat()
        with part.open('r+b') as stream:
            stream.write(b'CHANGED')
        if mutation[0] == 'rewrite_restore_mtime':
            os.utime(str(part), ns=(saved.st_atime_ns, saved.st_mtime_ns))
def racing_link(src, dst, **kwargs):
    if mutation[1] == 'before_link' and Path(dst).name == '0':
        change(src)
    result = real_link(src, dst, **kwargs)
    if mutation[1] == 'after_link' and Path(dst).name == '3':
        change(Path(src).parent/'0')
    return result
os.link = racing_link
''' % (mutation,)
        code = code.replace('dest = Path(sys.argv[1])', inject+'\ndest = Path(sys.argv[1])')
    script = root.parent/'acquire.sh'
    script.write_text('set -euo pipefail\n'+code+'\necho ACQUISITION_COMPLETE\n')
    env = dict(os.environ, E=str(dest), OBJECT=tiny['object'], KROOT=str(root),
               PATH=str(bin_dir)+':/usr/bin:/bin', PULL_LOG=str(root.parent/'pull.jsonl'), SEED=str(seed))
    for key in ('REUSE_PARTS_FROM', 'REUSE_SEARCH', 'FAIL_PULL'):
        env.pop(key, None)
    if reuse is not None:
        env['REUSE_PARTS_FROM'] = str(reuse)
    if search:
        env['REUSE_SEARCH'] = '1'
    if fail_pull is not None:
        env['FAIL_PULL'] = str(fail_pull)
    outcome = subprocess.run(['bash', str(script)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (root.parent/'stdout.txt').write_bytes(outcome.stdout)
    (root.parent/'stderr.txt').write_bytes(outcome.stderr)
    log = Path(env['PULL_LOG'])
    calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    return outcome, dest, calls


def rejected(label, defect=None, empty=False, failed_link=False, search=False):
    root = fixture(label)
    src = source(root, defect=defect)
    outcome, dest, calls = execute(root, '' if empty else (None if search else src),
                                  search=search, failed_link=failed_link)
    assert outcome.returncode != 0, label
    assert b'ACQUISITION_COMPLETE' not in outcome.stdout
    assert not calls, (label, calls)
    expected = 2 if failed_link else 0
    assert sum(os.path.lexists(str(dest/str(i))) for i in range(4)) == expected
    for i in range(expected):
        assert os.path.samefile(str(src/str(i)), str(dest/str(i)))
    assert not list(dest.glob('*.partial'))
    record(label+' (no pull/copy fallback)')


def mutation_rejected(kind, when):
    label = kind+'_'+when
    root = fixture(label)
    src = source(root, independent=True)
    outcome, dest, calls = execute(root, src, mutation=(kind, when))
    assert outcome.returncode != 0, (label, outcome.stdout, outcome.stderr)
    assert b'ACQUISITION_COMPLETE' not in outcome.stdout, label
    assert b'linked from' not in outcome.stdout, label
    assert outcome.stderr, label
    assert not calls, (label, calls)
    assert not list(dest.glob('*.partial')), label
    for i in range(4):
        part = dest/str(i)
        if os.path.lexists(str(part)):
            original = src/(str(i)+'.original')
            identities = [os.lstat(str(src/str(i))).st_ino]
            if original.exists():
                identities.append(original.stat().st_ino)
            assert os.lstat(str(part)).st_ino in identities, label
    record(label+' (refused; links retained; no fill/pull/copy fallback)')


def linked(label, search=False):
    root = fixture(label)
    if search:
        source(root, 'a15_cot_ap001_mismatch', 'marker')
        (root/'a15_cot_ap002_no_marker/a/e').mkdir(parents=True)
        # A later matching but invalid package must not displace the first match.
        source(root, 'a15_cot_ap999_invalid', 'size')
    src = source(root)
    outcome, dest, calls = execute(root, None if search else src, search=search)
    assert outcome.returncode == 0, outcome.stderr
    assert not calls
    assert all(os.path.samefile(str(src/str(i)), str(dest/str(i))) for i in range(4))
    expected = 'linked from %s; part 0 link count %d' % (src, (dest/'0').stat().st_nlink)
    assert outcome.stdout.decode().splitlines() == [expected, 'ACQUISITION_COMPLETE']
    record(label+' (four shared inodes; reported link count verified)')


def pulled(label, search=False, nested=False, fail=False, ignore_match=False):
    root = fixture(label)
    if nested:
        source(root/'nested')
        source(root, 'other_package')
        source(root, 'a15_cot_ap001_mismatch', 'marker')
    if ignore_match:
        source(root)
    outcome, dest, calls = execute(root, search=search, fail_pull=1 if fail else None)
    assert (outcome.returncode != 0) == fail, outcome.stderr
    assert len(calls) == (2 if fail else 4)
    for i, call in enumerate(calls):
        assert call == ['-o', 'Boto:num_retries=0', '-o', 'Boto:metadata_service_num_attempts=1',
                        '-o', 'GSUtil:parallel_process_count=1', '-o', 'GSUtil:parallel_thread_count=1',
                        '-o', 'GSUtil:sliced_object_download_threshold=0',
                        '-o', 'GSUtil:sliced_object_download_max_components=1', '-q', 'cp',
                        'gs://cmu-gpucloud-jjyeung/'+tiny['object']+'.part0%d-of-04' % i,
                        str(dest/(str(i)+'.partial'))]
    if fail:
        assert (dest/'0').is_file() and not (dest/'1').exists()
        assert b'ACQUISITION_COMPLETE' not in outcome.stdout
    else:
        for i in range(4):
            assert (dest/str(i)).read_bytes() == (seed/str(i)).read_bytes()
            assert (dest/str(i)).stat().st_nlink == 1
        assert 'pulled; part 0 link count 1' in outcome.stdout.decode().splitlines()
    record(label+' (original pull arguments; zero retries)')


record('only fill acquisition changed; four other generated scripts byte-identical')
record('current-script diff changes only reuse helper; all five scripts match generator')
record('Python 3.6.8 py_compile and five scripts plus rendered fill bash -n')
linked('explicit_reuse')
for label, defect in [('wrong_size', 'size'), ('symlink_part', 'symlink'), ('wrong_marker', 'marker'),
                      ('wrong_concat_sha', 'sha'), ('missing_part', 'missing'), ('directory_part', 'directory')]:
    rejected(label, defect)
rejected('empty_explicit_reuse', empty=True)
rejected('link_failure_after_two_links', failed_link=True)
for when in ('before_link', 'after_link'):
    for kind in ('replace', 'rewrite', 'rewrite_restore_mtime', 'symlink'):
        mutation_rejected(kind, when)
linked('search_first_matching_marker', search=True)
rejected('search_match_invalid_parts', defect='size', search=True)
root = fixture('explicit_precedence')
source(root)
bad = source(root, 'a15_cot_ap200', 'marker')
outcome, dest, calls = execute(root, bad, search=True)
assert outcome.returncode != 0 and not calls and not (dest/'0').exists()
record('explicit source overrides search; invalid explicit source stops')
pulled('pull_unset')
pulled('pull_search_no_match', search=True, nested=True)
pulled('pull_search_disabled', ignore_match=True)
pulled('pull_failure_no_retry', fail=True)
summary = dict(passed=True, cases=len(results), tests=results, run=str(RUN),
               synthetic_part_bytes=SIZE, production_part_bytes=5395758080,
               python=sys.version.split()[0], changed_scripts=[NAME])
(W/'RESULT.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n')
logs.append('PASS: %d cases; no SSH, network, Git, GPU, deletion or submission.' % len(results))
(W/'TEST_OUTPUT.txt').write_text('\n'.join(logs)+'\n')
print(logs[-1])
