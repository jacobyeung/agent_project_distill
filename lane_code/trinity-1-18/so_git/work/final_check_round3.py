"""Check final patch bytes, installed pins and workspace metadata without Git."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

L = Path('/scratch/jjyeung/orch_n30/so_git')
OUT = L / 'out'
root = Path(tempfile.mkdtemp(prefix='round3_final_', dir=str(L / 'work')))
pins = json.loads((OUT / 'PATCH_BASES.json').read_text())
validation = json.loads((OUT / 'evidence/round3_validation_result.json').read_text())
validated = Path(validation['root'])
commands = []

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def run(label, argv, cwd):
    argv = ['nice', '-n', '10'] + argv
    result = subprocess.run(argv, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            universal_newlines=True, timeout=30)
    name = 'evidence/round3_final_' + label + '.txt'
    (OUT / name).write_text(result.stdout)
    commands.append(dict(label=label, argv=argv, cwd=str(cwd), exit_code=result.returncode, exact_output=name))
    assert result.returncode == 0, (label, result.stdout)

for name, entry in pins.items():
    tree = root / name[:2]
    tree.mkdir()
    assert sha((OUT / 'patches' / name).read_bytes()) == entry['patch_sha256']
    pin = sha(json.dumps({p: r['before_sha256'] for p, r in entry['files'].items()},
                         sort_keys=True, separators=(',', ':')).encode())
    assert pin == entry['base_pin_sha256']
    for path, record in entry['files'].items():
        if record['before_sha256'] is None:
            continue
        if name.startswith(('01_', '03_')):
            source = L / 'in' / Path(path).name
        else:
            base = L / ('work/review_round2_base' if name.startswith('04_') else 'work/review_round3_base')
            source = base / (Path(path).name if path.startswith('docs/') else path)
        raw = source.read_bytes()
        assert sha(raw) == record['before_sha256'], str(source)
        target = tree / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    run('patch_' + name[:2], ['patch', '--batch', '--fuzz=0', '-p1', '-i', str(OUT / 'patches' / name)], tree)
    for path, record in entry['files'].items():
        raw = (tree / path).read_bytes()
        assert sha(raw) == record['after_sha256']
        if path.startswith('docs/'):
            delivery = OUT / Path(path).name
        elif path == 'test_recover_boundary_remediation.py':
            delivery = OUT / 'tests' / path
        elif path == 'tools/recover_boundary_remediation.py':
            delivery = L / 'work/review_round3_source' / path
        elif path == 'tools/lane_code_filter.py':
            delivery = validated / 'owner' / path
        else:
            delivery = OUT / path
        assert raw == delivery.read_bytes(), path

for path in (OUT / 'tools').iterdir():
    assert path.read_bytes() == (validated / 'owner/tools' / path.name).read_bytes()
for path in (OUT / 'tests').rglob('*'):
    if path.is_file():
        relative = path.relative_to(OUT / 'tests')
        other = (validated / 'distill/test_recover_boundary_remediation.py' if relative.name == 'test_recover_boundary_remediation.py'
                 else validated / 'owner/tests' / relative)
        assert path.read_bytes() == other.read_bytes(), str(relative)

source = L / 'work/review_round3_source'
lane = {}
for folder in ('tools', 'tests'):
    for path in (source / folder).rglob('*'):
        if path.is_file():
            relative = path.relative_to(source)
            if relative.as_posix() == 'tools/recover_boundary_remediation.py':
                checked = validated / 'distill' / relative
            elif relative.as_posix() == 'tests/test_recover_boundary_remediation.py':
                checked = validated / 'distill/test_recover_boundary_remediation.py'
            else:
                checked = validated / 'owner' / relative
            assert path.read_bytes() == checked.read_bytes(), str(relative)
            lane[str(relative)] = sha(path.read_bytes())
(OUT / 'evidence/round3_lane_source_hashes.json').write_text(json.dumps(lane, sort_keys=True, indent=2) + '\n')
for tag, py in (('py36', '/usr/bin/python3'), ('py312', '/scratch/jjyeung/envs/p1cpu/bin/python')):
    run('defaults_' + tag, [py, '-I', '-s', '-B', str(L / 'work/check_round3_defaults.py')], L)
run('lane_command_syntax', ['bash', '-n', str(L / 'work/round3_lane_command.txt')], L)
for path, record in json.loads((OUT / 'evidence/round3_installed_base.json').read_text()).items():
    assert sha(Path(path).read_bytes()) == record['sha256'], path
for name in ('lane_code_sync.sh', 'lane_code_scan.py'):
    assert (source / 'tools' / name).read_bytes() == (L / 'in' / name).read_bytes()
assert not (validated / 'git_attempts.txt').exists()
assert not (L / 'work/round3_guard/attempts.txt').exists()

# One local metadata-only inventory, without reading file bodies or following symlinks.
total, entries = 0, 0
pending = [str(L)]
while pending:
    directory = pending.pop()
    with os.scandir(directory) as items:
        for item in items:
            total += item.stat(follow_symlinks=False).st_size
            entries += 1
            if item.is_dir(follow_symlinks=False):
                pending.append(item.path)
assert total < 3_000_000_000, total
now = subprocess.check_output(['date', '-u'], universal_newlines=True).strip()
resources = dict(utc=now, measured_workspace_bytes=total, measured_workspace_entries=entries,
                 measured_scratch_available_bytes=shutil.disk_usage(str(L)).free,
                 scope='One local metadata inventory; symlinks not followed; before report/manifest writes.',
                 memory_peak='not measured', configured_memory_limit_bytes=30_000_000_000,
                 configured_thread_limit=8, torch_used=False)
(OUT / 'evidence/round3_resources.json').write_text(json.dumps(resources, indent=2) + '\n')
(OUT / 'evidence/round3_final_commands.json').write_text(json.dumps(commands, indent=2) + '\n')
result = dict(utc=now, root=str(root), final_patch_applications=5, patch_pins_valid=True,
              tools_and_tests_identical_to_validated_tree=True, installed_files_unchanged=True,
              hourly_unchanged=True, real_git_lane_source_matches_validated_tree=True,
              git_attempts=0, workspace_below_3GB=True)
(OUT / 'evidence/round3_final_result.json').write_text(json.dumps(result, indent=2) + '\n')
(L / 'work/STATUS.md').write_text(now + ': Final patch applications, source hashes and installed pins pass. All permitted dual-Python suites passed; no Git attempted. Report/manifest finalization remains.\n')
print(json.dumps(result))
print(json.dumps(resources))
