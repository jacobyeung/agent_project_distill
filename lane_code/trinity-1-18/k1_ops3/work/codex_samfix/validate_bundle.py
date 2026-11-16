"""Validate final target pins against the staged patch and unchanged executed files."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
KIT = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a')
MIRROR = Path('/scratch/jjyeung/orch_cd/k1_build/work/kit_k1a')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

old = json.loads((KIT/'out/DEPENDENCIES.json').read_text())
new = json.loads((ROOT/'DEPENDENCIES.json').read_text())
assert new == json.loads((ROOT/'patched/out/DEPENDENCIES.json').read_text())
assert len(old) == len(new) == 108
uninstalled, changed, external = [], [], []
for old_name, old_hash in old.items():
    source = Path(old_name)
    target = KIT/source.relative_to(MIRROR) if source.is_relative_to(MIRROR) else source
    assert sha(target) == old_hash, f'Original executed source was modified: {target}'
    staged = ROOT/'patched'/target.relative_to(KIT) if target.is_relative_to(KIT) else target
    actual = staged if staged.exists() else target
    assert sha(actual) == new[str(target)], f'Bad final pin: {target}'
    if old_hash != new[str(target)]: changed.append(str(target))
    if sha(target) != new[str(target)]: uninstalled.append(str(target))
    if not target.is_relative_to(KIT): external.append(str(target))
assert changed == uninstalled == [str(KIT/'native_kit/boundaries.py')]
assert len(external) == 15
record = dict(verified_overlay_sources=108, unchanged_original_sources=108,
              changed_hashes=changed, expected_predeployment_mismatches=uninstalled,
              relocated_kit_paths=93, actual_external_paths=external,
              final_dependencies_sha256=sha(ROOT/'DEPENDENCIES.json'),
              boundary_sha256=sha(ROOT/'patched/native_kit/boundaries.py'))
(ROOT/'receipts/bundle_validation.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(record, indent=2))
