"""Render the bounded report and validate its evidence artifact."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
j = json.loads((ROOT / 'out/GUARD.json').read_text())
a, b = j['captures']
assert len(a['rows']) == 2 and len(b['rows']) == 10
assert all(r['replay_matches'] for c in j['captures'] for r in c['rows'])
assert all(c['sealed_result'] == c['reviewed_result'] == c['gt_reviewed_up_axis_result'] ==
           c['gt_sealed_up_axis_result'] == 'reference_camera_up_opposes_gravity' for c in j['captures'])
assert all(not c['convert_geometry_export_exists'] for c in j['captures'])
assert j['summary']['two_refused']['answered'] == 11
for path in [ROOT / 'audit.py', ROOT / 'run.sh']:
    assert hashlib.sha256(path.read_bytes()).hexdigest() == j['input_sha256'][str(path)]

def vec(v): return '[' + ', '.join(f'{x:.8f}' for x in v) + ']'
def pair(r): return ' / '.join(r['operands'])
def values(r):
    pred = 'not seen' if r['prediction_m'] is None else f"{r['prediction_m']:.2f}"
    return f"{pred} / {r['corrected_label_m']:.6f}"

lines = [
    '**Verdict:** The reader is right to admit these orientations; the guard detects real camera roll but wrongly treats it as invalid geometry, and the reader’s distances remain inaccurate.',
    '**Fix:** Share one converter/reader contract that permits arbitrary roll and retains finite/rotation/intrinsic checks; diagnose gravity error separately and score distances against corrected labels.',
    '**Commands:** `bash run.sh audit.py > out/audit.log 2>&1` produces every number below and `out/GUARD.json`; `bash run.sh report.py` renders this report.',
    'OpenCV image-up is `[0,-1,0]`; the head predicts gravity-UP, not downward acceleration; dataset world-up is `[0,0,1]` (physical gravity direction `[0,0,-1]`).',
    '',
    '| Capture | Head gravity-up in reference camera | GT gravity-up in reference camera | Image-up angle to head / GT | Head–GT error |',
    '|---|---|---|---|---|',
]
for c in [a,b]:
    lines.append(f"| {c['capture'].split('/')[1]} | `{vec(c['gravity_head_raw'])}` | `{vec(c['gt_up_in_reference_camera'])}` | {c['predicted_image_up_vs_world_up_deg']:.4f}° / {c['gt_image_up_vs_world_up_deg']:.4f}° | {c['gravity_head_error_vs_gt_deg']:.4f}° |")
lines += [
    f"Their image-up vectors in served world coordinates are `{vec(a['image_up_served_world'])}` and `{vec(b['image_up_served_world'])}`, respectively.",
    'GUARD.json preserves full-precision reference matrices and all GT/served poses; GT up is normalized `R_GT[0].T @ [0,0,1]`; a separate measured gravity/IMU field is MISSING from both manifest GT NPZs.',
    '`0f69aefe3d`, frame 0: the bathroom is upside down (floor mat and toilet base at image top); GT confirms inversion, despite the head’s 32.73° error.',
    '`2c7c10379b`, frame 0: the living room is nearly sideways (rug/floor at image right); GT places image-up 1.93° past horizontal, agreeing with the head’s sign.',
    f"Convert’s sealed/reviewed checks both refuse: `-R[0,2,1]` is {a['guard_margin']:.8f} / {b['guard_margin']:.8f}; even GT fails ({a['gt_guard_margin']:.8f} / {b['gt_guard_margin']:.8f}); reviewed plane norms {a['reviewed_plane_norm']:.8f} / {b['reviewed_plane_norm']:.8f} exceed 0.3.",
    f"Convert retains REFUSED_GEOMETRY.npz and emits no geometry.npz; A4 drops that terminal check and serves G3T pose/depth rotated by checkpoint gravity, scaled once by own-depth median ratios ({a['served_scale']:.10f} / {b['served_scale']:.10f} after float32 exp).",
    'A4 reconstructs the identical unscaled camera arrays, selects candidates with `candidates_argmax`, lifts best-frame spread-filtered boxes, and computes `box_grid_5cm` gaps; CPU replay matches all 12 responses (stored step-544 tensors, no fresh prefill).',
    '',
    '| Capture | Operand pairs (same order) | Served / corrected GT distance, metres |',
    '|---|---|---|',
]
# One row for the bathroom and five rows for the living room retain every answer.
for c in [a,b]:
    for k in range(0,len(c['rows']),2):
        rows=c['rows'][k:k+2]
        lines.append(f"| {c['capture'].split('/')[1]} | {'; '.join(map(pair, rows))} | {'; '.join(map(values, rows))} |")
lines += [
    'The two captures score **24.17% MRA** (30.00% bathroom; 23.00% living room), versus **57.15%** for 1,025 rows in 207 other K1 training captures and **54.06%** for 609 rows in 58 other ScanNet++ captures; only 2/11 answers have <25% relative error.',
    'MRA averages strict relative-error passes at 50%,45%,…,5%, with refusals scoring zero; answered-only MRA is 26.36% versus 59.17% on other K1 rows (57.35% on other ScanNet++ rows); these comparisons do not isolate gravity’s contribution to distance error.',
]
# Collapse the repeated table lead-in spacing to satisfy the requested line budget.
lines = [line for line in lines if line != '']
assert len(lines) <= 25, len(lines)
(ROOT / 'out/GUARD_VS_READER.md').write_text('\n'.join(lines)+'\n')
(ROOT / 'STATUS.md').write_text('Complete: out/GUARD_VS_READER.md and out/GUARD.json document both captures, exact vectors and poses, GT guard counterchecks, 12/12 CPU response parity, corrected-label accuracy, comparison with other K1 training captures, and SHA256 input provenance. The reader correctly permits these orientations, but its 11 answered rows score only 26.36% answered-only MRA; no runtime source or external file was changed.\n')
print(f"PASS: {len(lines)} report lines; 12 response checks; {len(j['input_sha256'])} input hashes.")
