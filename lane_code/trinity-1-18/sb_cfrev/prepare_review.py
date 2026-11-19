from pathlib import Path
import hashlib, json, shutil, subprocess

ROOT = Path(__file__).resolve().parent
A4 = Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/A4')
BUILD = Path('/scratch/jjyeung/orch_n30/sb_cachefix')
pins = {}
def read(p):
    data = p.read_bytes()
    pins[str(p)] = hashlib.sha256(data).hexdigest()
    return data

for d in ('work', 'logs', 'evidence'):
    (ROOT/d).mkdir(exist_ok=True)
for arm in ('orig', 'patched'):
    shutil.copytree(A4/'src', ROOT/'work'/arm/'src')
for p in (A4/'src').rglob('*'):
    if p.is_file():
        read(p)
patch = read(BUILD/'out/cachefix.patch')
(ROOT/'work/cachefix.patch').write_bytes(patch)
done = subprocess.run(['patch', '-p1', '--batch', '--fuzz=0', '-i', str(ROOT/'work/cachefix.patch')],
                      cwd=ROOT/'work/patched', capture_output=True, text=True)
(ROOT/'logs/apply.log').write_text(done.stdout+done.stderr)
assert done.returncode == 0, done
test = read(BUILD/'work/test_cachefix.py').decode()
test = test.replace("A4 = Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/A4/src/tree/student_pilot')", "A4 = HERE/'orig/src/tree/student_pilot'")
(ROOT/'work/test_cachefix.py').write_text(test)
diag = read(BUILD/'work/k1diag.py').decode()
diag = diag.replace("'fixed': (True, 'raw')", "'fixed': (True, 'kbox')")
diag = diag.replace("if patched:\n    for module", "for_override = PATCHED if patched else HERE/'orig/src/tree/student_pilot'\nif True:\n    for module")
diag = diag.replace("PATCHED/f'{module}.py'", "for_override/f'{module}.py'")
diag = diag.replace("(PATCHED if patched else Path(R.TREE)/'student_pilot').resolve()", "for_override.resolve()")
diag = diag.replace("common = dict(R.PINS)", """for m in list(sys.modules.values()):
        p = getattr(m, '__file__', None)
        if p and str(p).startswith('/scratch/jjyeung/') and p.endswith('.py') and '/envs/' not in p:
            R.read(p)
    R.read(__file__)
    common = dict(R.PINS)""")
diag = diag.replace("stats = dict(mixed_frames=0)", """stats = dict(mixed_frames=0)
        for n in {n for r in rows for n in r['operands']}:
            for frame in predicted.cache_detect(cache)(n):
                stats['mixed_frames'] += len({v['presence'] for v in frame}) > 1""")
diag = diag.replace("record = dict(capture=", "record = dict(input_sha256=dict(R.PINS), capture=")
(ROOT/'work/k1diag.py').write_text(diag)
for rel in ('out/CACHEFIX_REPORT.md', 'review/REVIEW.md', 'out/sb_cachefix.tar', 'out/sb_cachefix.tar.sha256', 'work/scan_mixing.py', 'work/k1compare.py'):
    read(BUILD/rel)
assert pins[str(BUILD/'out/sb_cachefix.tar')].startswith('ebbd8d42')
for p in (ROOT/'work').glob('*.py'):
    read(p)
read(Path(__file__))
(ROOT/'evidence/preparation.json').write_text(json.dumps(dict(input_sha256=pins, patch_applied=True, archive_sha256=pins[str(BUILD/'out/sb_cachefix.tar')]), indent=2)+'\n')
(ROOT/'STATUS.md').write_text('Code-path review confirms one presence per served name/frame; the SAM memo stores encoder features only, and A4 enables only G3T memoization. The A4 source is copied locally and the exact patch applies without fuzz. Independent tests, patch-only K1 parity, mutations, and journal audit remain in progress.\n')
print('Prepared local A4 copies and patch-only parity runner; archive', pins[str(BUILD/'out/sb_cachefix.tar')])
