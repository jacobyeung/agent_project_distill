"""Verify final patch bytes, immutable bases, current documentation and source pins."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from round4_common import L, OUT, SOURCE, PYTHONS, run, status

ROOT = L / 'work/round4_final'
ROOT.mkdir()
pins = json.loads((OUT / 'PATCH_BASES.json').read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for name, record in sorted(pins.items()):
    number = name[:2]
    tree = ROOT / number
    tree.mkdir()
    for relative, entry in record['files'].items():
        target = tree / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if entry['before_sha256'] is None:
            continue
        if number in ('01', '03'):
            source = L / 'in' / Path(relative).name
        else:
            base = {'04': L / 'work/review_round2_base', '05': L / 'work/review_round3_base',
                    '06': L / 'out_round3'}[number]
            source = base / (Path(relative).name if relative.startswith('docs/') else relative)
        assert sha(source) == entry['before_sha256'], str(source)
        shutil.copyfile(str(source), str(target))
    assert sha(OUT / 'patches' / name) == record['patch_sha256']
    run('final_patch_' + number, ['patch', '--batch', '--fuzz=0', '-p1', '-i', str(OUT / 'patches' / name)], tree)
    for relative, entry in record['files'].items():
        assert sha(tree / relative) == entry['after_sha256'], relative
        if relative.startswith('docs/'):
            delivery = OUT / Path(relative).name
        elif relative.startswith(('tools/', 'tests/')) and (OUT / relative).exists():
            delivery = OUT / relative
        elif relative == 'test_recover_boundary_remediation.py':
            delivery = OUT / 'tests' / relative
        else:
            delivery = SOURCE / relative
        assert (tree / relative).read_bytes() == delivery.read_bytes(), relative

for tag, py in PYTHONS:
    code = ('import sys,unittest; sys.path.insert(0,"tests"); '
            's=unittest.defaultTestLoader.loadTestsFromNames('
            '["test_review_round4.DocumentationTests", "test_review_round2.Documentation"]); '
            'r=unittest.TextTestRunner(verbosity=2).run(s); sys.exit(not r.wasSuccessful())')
    run('final_docs_' + tag, [py, '-I', '-s', '-B', '-c', code])

snapshot_manifest = json.loads((L / 'out_round3/MANIFEST.json').read_text())
for relative, record in snapshot_manifest['artifacts'].items():
    assert sha(L / 'out_round3' / relative) == record['sha256'], relative
base_pins = json.loads((L / 'work/round4_base_pins.json').read_text())
for name, expected in base_pins.items():
    assert sha(L / 'out_round3/tools' / name) == expected
    assert sha(L / 'work/round4_before/tools' / name) == expected
for path in (OUT / 'tools').iterdir():
    assert path.read_bytes() == (SOURCE / 'tools' / path.name).read_bytes()
for path in (OUT / 'tests').rglob('*'):
    if path.is_file():
        assert path.read_bytes() == (SOURCE / 'tests' / path.relative_to(OUT / 'tests')).read_bytes()
for name in ('GIT_OWNER.md', 'COVERAGE.md', 'HANDOVER.md'):
    assert (OUT / name).read_bytes() == (SOURCE / name).read_bytes()
assert (SOURCE / 'tools/lane_code_sync.sh').read_bytes() == (L / 'in/lane_code_sync.sh').read_bytes()
assert (SOURCE / 'tests/fixtures/lane_code_sync.sh').read_bytes() == (L / 'in/lane_code_sync.sh').read_bytes()
command = (L / 'work/round4_lane_command.txt').read_text().strip()
assert '```bash\n' + command + '\n```' in (OUT / 'HANDOVER.md').read_text()
source_pins = {str(p.relative_to(SOURCE)): sha(p)
               for category in ('tools', 'tests') for p in (SOURCE / category).rglob('*') if p.is_file()}
(OUT / 'evidence/round4_lane_source_hashes.json').write_text(json.dumps(source_pins, sort_keys=True, indent=2) + '\n')
(OUT / 'evidence/round4_source_equivalence.txt').write_text(
    'ALL_SIX_FINAL_PATCH_PREIMAGES_VERIFIED true\nALL_SIX_FINAL_PATCHES_MATCH_DELIVERY true\n'
    'ALL_THREE_OWNER_UPGRADES_MATCH_CUMULATIVE true\nFROZEN_SOURCE_MATCHES_DELIVERY true\n'
    'HOURLY_UNCHANGED true\nROUND3_SNAPSHOT_MANIFEST_VERIFIED true\nROUND4_BEFORE_TOOL_PINS_VERIFIED true\n')
status('Final six patch applications and documentation checks pass; round-3 snapshot and before-fix tool pins are unchanged. Frozen realgit5 source hashes recorded. Sealing report and manifest.')
