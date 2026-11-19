"""Build the cumulative patch against immutable input; verify a fresh application."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
INPUT = Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/corpusin')
TOOL = ROOT / 'work/tool'
CHECK = ROOT / 'work/patchcheck_round3'
PATCH = ROOT / 'out/patches/01_ingest_review2.diff'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

originals = sorted(p.relative_to(INPUT) for p in INPUT.rglob('*') if p.is_file())
delivered = sorted(p.relative_to(TOOL) for p in TOOL.rglob('*') if p.is_file())
assert len(originals) == 18
assert set(originals) <= set(delivered)
parts, changed, unchanged = [], [], []
for name in delivered:
    old = (INPUT / name).read_text() if name in originals else ''
    new = (TOOL / name).read_text()
    if old == new:
        unchanged.append(str(name))
        continue
    parts.extend(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                 fromfile='a/' + str(name) if name in originals else '/dev/null', tofile='b/' + str(name)))
    changed.append(dict(path=str(name), input_sha256=sha(INPUT / name) if name in originals else None,
                        output_sha256=sha(TOOL / name)))
PATCH.write_text(''.join(parts))
CHECK.mkdir()
for name in originals:
    target = CHECK / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(INPUT / name, target)
result = subprocess.run(['nice', '-n', '10', 'patch', '--batch', '--forward', '--no-backup-if-mismatch',
                         '-p1', '-d', str(CHECK)], input=PATCH.read_bytes(), stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
print(result.stdout.decode(), end='')
assert result.returncode == 0, result.returncode
for name in delivered:
    assert (CHECK / name).read_bytes() == (TOOL / name).read_bytes(), name
summary = dict(patch=str(PATCH.relative_to(ROOT)), patch_bytes=PATCH.stat().st_size, patch_sha256=sha(PATCH),
               input_root=str(INPUT), fixed_root=str(TOOL), patchcheck_root=str(CHECK),
               changed_files=changed, unchanged_files=unchanged, original_files=len(originals),
               delivered_files=len(delivered), applied_files_identical=len(delivered))
(ROOT / 'work/evidence/package_round3.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
print('PATCH: %d bytes; SHA256=%s' % (summary['patch_bytes'], summary['patch_sha256']))
print('INPUT: %d files; %d changed existing files; %d unchanged; %d new test files' %
      (len(originals), len(originals)-len(unchanged), len(unchanged), len(delivered)-len(originals)))
print('APPLIED: all %d delivered files match the work tool byte for byte' % len(delivered))
