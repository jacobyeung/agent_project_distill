"""Reproduce independent unified patches from the reviewed working tree."""
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest_path = ROOT / 'out/patches/manifest.json'
manifest = json.loads(manifest_path.read_text())
for name, item in manifest.items():
    if not name.endswith('.diff'):
        continue
    chunks = []
    for relative in item['paths']:
        original = ROOT / 'in/tree/work/tree_r1' / relative
        modified = ROOT / 'work/tree' / relative
        # This file contains changes from two independent patches in work/tree.
        # Preserve each patch's original isolated hunks, verified against input.
        if relative == 'student_pilot/carrier_c1_run.py':
            modified = ROOT / 'work/verified' / Path(name).stem / relative
        chunks.extend(difflib.unified_diff(
            original.read_text().splitlines(keepends=True) if original.exists() else [],
            modified.read_text().splitlines(keepends=True),
            fromfile='a/' + relative if original.exists() else '/dev/null',
            tofile='b/' + relative))
    payload = ''.join(chunks).encode()
    (ROOT / 'out/patches' / name).write_bytes(payload)
    item.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
manifest['_application'] = {
    'method': 'Each diff applies independently to the untouched input with patch --batch --fuzz=0 -p1. For the complete tested build, apply 01, 02, 03 in order to one fresh input copy; offsets are permitted, fuzz is not.',
    'test_method': 'Run tests.test_so_prefetch, tests.test_so_cache, tests.test_so_metrics and tests.test_so_joint on the complete series. Shared test helpers ship in 01; the joint regression in 03 requires all three patches.',
    'defaults': {'C1_CPU_PREFETCH': '0', 'C1_DECODED_CACHE_MIB': '0', 'C1_BATCH_METRICS': '0'},
}
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
