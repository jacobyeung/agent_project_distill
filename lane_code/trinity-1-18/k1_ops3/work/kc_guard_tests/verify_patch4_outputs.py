"""Verify completed bound receipts and preserve the protected-source proof."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
before = json.loads((ROOT / 'patch4_identity_before.json').read_text())
after = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before}
assert before == after
(ROOT / 'patch4_identity_proof.json').write_text(json.dumps(
    dict(before=before, after=after, files=len(before), all_equal=True), indent=2)+'\n')
(ROOT / 'patch4_bound_identity_proof.json').write_bytes((ROOT / 'identity_proof.json').read_bytes())
paths = ['patch4_primary296/tables/TABLE_RECEIPT.json',
         'patch4_sensitivity300/tables/TABLE_RECEIPT.json',
         'patch4_canvas/landscape_after/TABLE_RECEIPT.json',
         'patch4_canvas/render_tables/TABLE_RECEIPT.json',
         'patch4_canvas/render_fixture/RENDER_RECEIPT.json']
for interpreter in ('sam3', 'p1cpu'):
    for stage in ('tables', 'passing_tables', 'render', 'passing_render'):
        name = 'TABLE_RECEIPT.json' if 'tables' in stage else 'RENDER_RECEIPT.json'
        paths.append(f'patch4_unit_{interpreter}/{stage}/{name}')
receipts = {}
for path in paths:
    r = json.loads((ROOT / path).read_text())
    assert r['json_bound_bytes'] == 67_108_864, path
    receipts[path] = r['json_bound_bytes']
for name, count in (('primary296', 296), ('sensitivity300', 300)):
    out = ROOT / ('patch4_' + name) / 'tables'
    r = json.loads((out / 'TABLE_RECEIPT.json').read_text())
    g = json.loads((out / 'GUARD_REPORT.json').read_text())['K1']
    assert len(r['gt_canvas_map']) == len(g['captures']) == count
    assert set(r['gt_canvas_map']) == set(g['captures'])
    assert sum(r['gt_canvas_map_counts'].values()) == count
record = dict(protected_files_equal=len(before), receipts=receipts,
              full_capture_counts=[296, 300], all_passed=True)
(ROOT / 'patch4_output_verification.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(record))
