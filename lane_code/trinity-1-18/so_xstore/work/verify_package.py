"""Apply the delivered patch to a fresh base and run the delivered tests."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import resource
import shutil
import subprocess
import sys

L = Path(__file__).resolve().parent.parent
info = json.loads((L / 'work/BASE.json').read_text())
assert info['build'] == '21b' and (L / 'in/tree21b/READY').is_file()
manifest = json.loads((L / 'out/patches/manifest.json').read_text())
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
target = L / 'work' / ('verified_' + stamp)
shutil.copytree(info['root'], target, ignore=shutil.ignore_patterns('.git', '__pycache__', 'artifacts'))
log_dir = L / 'out/tests' / stamp
log_dir.mkdir()
results = []
for name, entry in manifest.items():
    patch = L / 'out/patches' / name
    assert hashlib.sha256(patch.read_bytes()).hexdigest() == entry['sha256']
    command = ['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch)]
    p = subprocess.run(command, cwd=target, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (log_dir / 'apply.txt').write_text(p.stdout)
    print(p.stdout, end='', flush=True)
    assert p.returncode == 0
    for path, digest in entry['files'].items():
        assert hashlib.sha256((target / path).read_bytes()).hexdigest() == digest
inventory = json.loads((L / 'out/evidence/base_inventory.json').read_text())
for name, digest in inventory.items():
    assert hashlib.sha256((target / name).read_bytes()).hexdigest() == digest
print(f'PASS: {len(inventory)} original files remain byte-identical; all patch files match manifest.', flush=True)
for test in ('test_preparation_store.py', 'test_preparation_native_boundary.py'):
    command = [sys.executable, '-I', '-s', '-B', str(target / 'tests' / test), '-v']
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    p = subprocess.run(command, cwd=target, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=os.environ.copy(), timeout=180)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    (log_dir / (test + '.txt')).write_text(p.stdout)
    print('\n'.join(p.stdout.splitlines()[-5:]), flush=True)
    results.append(dict(command=command, exit_code=p.returncode, log=str(log_dir / (test + '.txt')),
                        summary=p.stdout.splitlines()[-4:],
                        child_user_seconds=after.ru_utime-before.ru_utime,
                        cumulative_children_peak_rss_kib=after.ru_maxrss))
    assert p.returncode == 0
receipt = dict(status='PASS', base=info, tree=str(target), original_files_unchanged=len(inventory),
               results=results, scope='Groundwork and native boundary tests only; no native store/adopt loss proof.')
(L / 'out/tests/VERIFICATION.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
