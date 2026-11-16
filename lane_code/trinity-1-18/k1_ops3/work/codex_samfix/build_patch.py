"""Build the review bundle without modifying the executing kit or mirror."""
from pathlib import Path
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parent
KIT = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a')
MIRROR_KIT = Path('/scratch/jjyeung/orch_cd/k1_build/work/kit_k1a')
SCRATCH = ROOT / 'scratch_kit'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

relative = Path('native_kit/boundaries.py')
before = (KIT / relative).read_text()
after = before.replace(
    "  if self.sam_model is not None:self.sam_model._backend.model.to('cpu')",
    "  if self.sam_model is not None:\n"
    "   import torch\n"
    "   # SAM loads inference tensors lazily; preserve that state across device copies.\n"
    "   with torch.inference_mode():self.sam_model._backend.model.to('cpu')",
).replace(
    "  else:self.sam_model._backend.model.to(self.device)",
    "  else:\n"
    "   with torch.inference_mode():self.sam_model._backend.model.to(self.device)",
)
assert before != after
assert after.count('with torch.inference_mode():') == 2
write(ROOT / 'patched' / relative, after.encode())
old_pins = json.loads((KIT / 'out/DEPENDENCIES.json').read_text())
pins, audit = {}, []
for old, expected in old_pins.items():
    old_path = Path(old)
    # External runtime dependencies remain at their actual mirror paths.
    path = KIT / old_path.relative_to(MIRROR_KIT) if old_path.is_relative_to(MIRROR_KIT) else old_path
    data = path.read_bytes()
    assert sha(data) == expected, f'Existing executed source differs from old pin: {path}'
    changed = path == KIT / relative
    pins[str(path)] = sha(after.encode()) if changed else expected
    audit.append(dict(old_path=old, executed_path=str(path), old_sha256=expected,
                      new_sha256=pins[str(path)], changed=changed))
pin_data = (json.dumps(pins, indent=2) + '\n').encode()
write(ROOT / 'patched/out/DEPENDENCIES.json', pin_data)
write(ROOT / 'DEPENDENCIES.json', pin_data)
patch = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                   fromfile='a/'+str(relative), tofile='b/'+str(relative)))
write(ROOT / 'fix.diff', patch.encode())
pin_diff = ''.join(difflib.unified_diff((KIT/'out/DEPENDENCIES.json').read_text().splitlines(True),
                                     pin_data.decode().splitlines(True),
                                     fromfile='a/out/DEPENDENCIES.json', tofile='b/out/DEPENDENCIES.json'))
write(ROOT / 'dependencies.diff', pin_diff.encode())
files = [p for sub in ('native_kit', 'work') for p in (KIT/sub).rglob('*')
         if p.is_file() and p.suffix in ('.py', '.sh')]
assert sum(p.stat().st_size for p in files) < 2_000_000
for path in files:
    write(SCRATCH / path.relative_to(KIT), path.read_bytes())
write(SCRATCH / relative, after.encode())
# The test copy must verify its own sources, rather than the unpatched production kit.
test_pins = {str(SCRATCH/Path(p).relative_to(KIT)) if Path(p).is_relative_to(KIT) else p: h
             for p, h in pins.items()}
write(SCRATCH/'out/DEPENDENCIES.json', (json.dumps(test_pins, indent=2)+'\n').encode())
receipt = dict(pin_count=len(pins), relocated_kit_pins=sum(a['old_path'] != a['executed_path'] for a in audit),
               changed_hashes=[a for a in audit if a['changed']], pins=audit,
               scratch_source_files=len(files), scratch_source_bytes=sum(p.stat().st_size for p in files))
write(ROOT/'receipts/pins.json', (json.dumps(receipt, indent=2)+'\n').encode())
print(json.dumps({k:v for k,v in receipt.items() if k != 'pins'}, indent=2))
