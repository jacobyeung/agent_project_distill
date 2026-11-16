"""Write the deployment pins, difflib patch, and receipt identity proof."""
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a')
PATCHED = ROOT / 'kit_k1a'
EVIDENCE = ROOT / 'evidence'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (EVIDENCE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


dep_rel = 'out/DEPENDENCIES.json'
cli_rel = 'work/k1_cli.py'
original_dep_sha = sha(ORIGINAL / dep_rel)
assert original_dep_sha == 'c0c81f33a1cc671b6040244d80d47d902ebc7182f77345c1dc1c46f28897c283'
old_text = (ORIGINAL / dep_rel).read_text()
old_pins = json.loads(old_text)
cli_key = str(ORIGINAL / cli_rel)
assert sha(ORIGINAL / cli_rel) == old_pins[cli_key]
new_cli_sha = sha(PATCHED / cli_rel)
assert old_text.count(old_pins[cli_key]) == 1
new_text = old_text.replace(old_pins[cli_key], new_cli_sha)
new_pins = json.loads(new_text)
assert old_pins.keys() == new_pins.keys()
assert [p for p in old_pins if old_pins[p] != new_pins[p]] == [cli_key]
(PATCHED / dep_rel).write_text(new_text)

verified = []
for path, old_hash in old_pins.items():
    source = Path(path)
    assert sha(source) == old_hash, path
    target = PATCHED / source.relative_to(ORIGINAL) if source.is_relative_to(ORIGINAL) else source
    assert sha(target) == new_pins[path], path
    verified.append({'deployment_path': path, 'checked_path': str(target), 'sha256': new_pins[path]})
save('verified_pins.json', verified)

inventory = json.loads((EVIDENCE / 'copied_files.json').read_text())
changed = []
for relative, expected in inventory.items():
    assert sha(ORIGINAL / relative) == expected, relative
    if sha(PATCHED / relative) != expected:
        changed.append(relative)
assert sorted(changed) == sorted([cli_rel, dep_rel]), changed

before = json.loads((EVIDENCE / 'identity_before.json').read_text())
after = json.loads((EVIDENCE / 'identity_after.json').read_text())
original = json.loads((EVIDENCE / 'identity_original.json').read_text())
assert before == after
normalized = {
    str(ORIGINAL / Path(p).relative_to(PATCHED)) if Path(p).is_relative_to(PATCHED) else p: h
    for p, h in after['source_identity'].items()
}
assert normalized == original['source_identity']
assert after['producer_sha256'] == original['producer_sha256']
assert after['bindings_module'] == str(PATCHED / 'native_kit/bindings.py')
assert cli_key not in original['source_identity']
assert str(ORIGINAL / dep_rel) not in original['source_identity']
save('identity_proof.json', {
    'same_scratch_location_before_after_equal': before == after,
    'source_identity_entries': len(normalized),
    'original_identity_equal_after_scratch_prefix_mapping': normalized == original['source_identity'],
    'producer_sha256_original': original['producer_sha256'],
    'producer_sha256_patched': after['producer_sha256'],
    'original_path_source_identity': normalized,
    'changed_copied_files': sorted(changed),
    'all_original_copied_files_still_match': True,
    'original_pins_verified': len(old_pins),
    'patched_pins_verified_with_scratch_mapping': len(verified),
    'halted_root_accessed': False,
    'receipt_scope': 'Source and producer identities remain valid at the original deployment paths; no halted-root receipt payloads were reread.',
})

patch = ''
for rel in [cli_rel, dep_rel]:
    patch += ''.join(difflib.unified_diff(
        (ORIGINAL / rel).read_text().splitlines(keepends=True),
        (PATCHED / rel).read_text().splitlines(keepends=True),
        fromfile='a/kit_k1a/' + rel, tofile='b/kit_k1a/' + rel))
(ROOT / 'max-bytes.diff').write_text(patch)
pins = {
    'original_dependencies_sha256': original_dep_sha,
    'new_dependencies_sha256': sha(PATCHED / dep_rel),
    'original_k1_cli_sha256': old_pins[cli_key],
    'new_k1_cli_sha256': new_cli_sha,
    'unchanged_k1_phases_sha256': after['producer_sha256'],
    'diff_sha256': sha(ROOT / 'max-bytes.diff'),
}
save('new_pins.json', pins)
print(json.dumps(pins, indent=2))
print(f'PASS: {len(verified)} pins; {len(normalized)} source identities; only CLI and its dependency pin changed.')
