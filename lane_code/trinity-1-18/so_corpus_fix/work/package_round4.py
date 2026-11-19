"""Package independently selectable patches against the immutable input tree."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
INPUT = Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/corpusin')
TOOL = ROOT / 'work/tool'
CORE = ROOT / 'work/patchcheck_round4_core'
FULL = ROOT / 'work/patchcheck_round4_full'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


groups = {
    '01_ingest_review2.diff': ['ingest_read.py', 'SCHEMA.md', 'HOWTO.md',
                              'tests/test_review2.py', 'tests/test_review3.py'],
    '02_add_read_review2.diff': ['add_read.sh', 'tests/test_new_read_wrapper.py'],
    '03_kit_alias_proof.diff': ['prove_kit_alias_ids.py', 'tests/test_kit_alias_proof.py'],
}
patches = []
for name, paths in groups.items():
    parts = []
    for path in paths:
        original = INPUT / path
        old = original.read_text() if original.exists() else ''
        new = (TOOL / path).read_text()
        parts.extend(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                     fromfile='a/' + path if original.exists() else '/dev/null', tofile='b/' + path))
    patch = ROOT / 'out/patches' / name
    patch.write_text(''.join(parts))
    patches.append(dict(path=str(patch.relative_to(ROOT)), bytes=patch.stat().st_size,
                        sha256=sha(patch), files=paths))


def apply(name, target):
    result = subprocess.run(['nice', '-n', '10', 'patch', '--batch', '--forward',
                             '--no-backup-if-mismatch', '-p1', '-d', str(target)],
                            input=(ROOT / 'out/patches' / name).read_bytes(),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout.decode(), end='')
    assert result.returncode == 0, result.returncode


shutil.copytree(INPUT, CORE)
apply('01_ingest_review2.diff', CORE)
assert (CORE / 'add_read.sh').read_bytes() == (INPUT / 'add_read.sh').read_bytes()
print('CORE: wrapper remains byte-identical to input')
shutil.copytree(CORE, FULL)
apply('02_add_read_review2.diff', FULL)
apply('03_kit_alias_proof.diff', FULL)
originals = sorted(p.relative_to(INPUT) for p in INPUT.rglob('*') if p.is_file())
delivered = sorted(p.relative_to(TOOL) for p in TOOL.rglob('*') if p.is_file())
assert set(originals) <= set(delivered)
changes = {p for paths in groups.values() for p in paths}
unchanged = []
for name in delivered:
    assert (FULL / name).read_bytes() == (TOOL / name).read_bytes(), name
    if str(name) not in changes:
        assert (INPUT / name).read_bytes() == (TOOL / name).read_bytes(), name
        unchanged.append(str(name))
assert len(originals) == 18
print('FULL: all %d delivered files match the work tool byte for byte' % len(delivered))
print('INPUT: %d files; %d unchanged; %d modified; %d added' %
      (len(originals), len(unchanged), len(originals) - len(unchanged), len(delivered) - len(originals)))
for patch in patches:
    print('%s: %d bytes; SHA256=%s' % (patch['path'], patch['bytes'], patch['sha256']))
scripts = ROOT / 'out/scripts'
scripts.mkdir(exist_ok=True)
shutil.copyfile(TOOL / 'prove_kit_alias_ids.py', scripts / 'prove_kit_alias_ids.py')
summary = dict(patches=patches, input_root=str(INPUT), core_root=str(CORE), full_root=str(FULL),
               input_files=len(originals), delivered_files=len(delivered), unchanged_files=unchanged,
               input_hashes={str(p): sha(INPUT / p) for p in originals},
               output_hashes={str(p): sha(TOOL / p) for p in delivered})
(ROOT / 'work/evidence/package_round4.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
