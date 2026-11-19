from pathlib import Path
import ast
import datetime
import hashlib
import json
import re

L = Path(__file__).resolve().parent.parent
manifest = json.loads((L / 'out/patches/manifest.json').read_text())
verification = json.loads((L / 'out/tests/VERIFICATION.json').read_text())
base = Path(verification['base']['root'])
inventory = json.loads((L / 'out/evidence/base_inventory.json').read_text())
for name, expected in inventory.items():
    assert hashlib.sha256((base / name).read_bytes()).hexdigest() == expected
    assert hashlib.sha256((L / 'work/tree' / name).read_bytes()).hexdigest() == expected
for name, entry in manifest.items():
    assert hashlib.sha256((L / 'out/patches' / name).read_bytes()).hexdigest() == entry['sha256']
    for relative, expected in entry['files'].items():
        path = L / 'work/tree' / relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
        ast.parse(path.read_text(), filename=str(path))
        assert hashlib.sha256((Path(verification['tree']) / relative).read_bytes()).hexdigest() == expected
for document in ('REPORT.md', 'ADMISSION_ARGUMENT.md', 'NOTE_FOR_TREE_REBUILD.md', 'INPUT_AUDIT.md'):
    path = L / 'out' / document
    text = path.read_text()
    for link in re.findall(r'\]\(([^)]+)\)', text):
        if not link.startswith(('http://', 'https://')):
            assert (path.parent / link).exists(), (document, link)
assert (L / 'out/REPORT.md').read_text().startswith('VERDICT: PARTIAL ')
assert verification['status'] == 'PASS' and all(r['exit_code'] == 0 for r in verification['results'])
count = sum(int(re.search(r'Ran (\d+) tests', '\n'.join(r['summary'])).group(1)) for r in verification['results'])
assert count == 47
fixture = json.loads((L / 'out/evidence/cold_fixture.json').read_text())
assert fixture['results'][0]['root_digest'] == fixture['results'][1]['root_digest']
assert fixture['results'][0]['hostname'] != fixture['results'][1]['hostname']
assert fixture['results'][0]['tmpdir'] != fixture['results'][1]['tmpdir']
result = dict(status='PASS', scope='artifact integrity only; implementation verdict remains PARTIAL',
              time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              base=verification['base'], original_files_unchanged=len(inventory), tests_passed=count,
              links_exist=True, patch_and_source_hashes_match=True, source_parses=True,
              native_adopter_implemented=False, native_first_loss_proof=False,
              native_two_node_proof=False, protocol_fixture_roots_equal=True)
(L / 'out/FINAL_ARTIFACT_AUDIT.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
