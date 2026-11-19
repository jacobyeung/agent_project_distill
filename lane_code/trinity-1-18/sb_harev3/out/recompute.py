"""Bounded CPU audit of pinned specs; reuse prior helpers and budget simulation.

No raw evaluation inputs are read and no route look is consumed.
"""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / 'sb_harev/out'
V2 = ROOT.parent / 'sb_harev2/out'
CMD = 'OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /usr/bin/python3 out/recompute.py'
INPUTS, RESULTS = {}, []

# Only import pure definitions; never execute either earlier audit's file scans.
old_bytes = (OLD / 'recompute.py').read_bytes()
old_ast = ast.parse(old_bytes)
helpers = ast.Module(body=[n for n in old_ast.body if isinstance(n, ast.FunctionDef)
                          and n.name in {'read', 'js', 'result'}], type_ignores=[])
exec(compile(helpers, str(OLD / 'recompute.py'), 'exec'), globals())
INPUTS[str(OLD / 'recompute.py')] = {
    'sha256': hashlib.sha256(old_bytes).hexdigest(), 'bytes': len(old_bytes)}
v2_code = read(V2 / 'recompute.py')
v2_ast = ast.parse(v2_code)
read(OLD / 'REVIEW_VERDICT.md')
read(V2 / 'REVIEW_VERDICT.md')
read(V2 / 'SELECTION_INVENTORY.md')
prior = js(V2 / 'RECOMPUTE.json')

pins = {
    'HEAD_ACCURACY_DESIGN_20261119.md': 'abf002c71c27dbfbe1826301a1a5451f72935ba07985ffa4043e5ad707f014e5',
    'KIT_SPEC_box_ladder_k1_v2.md': '7ed6c03d5500a54c90cf156cf32d71b32e9fc2329876879c8d7bf9a907f1f3f0',
    'KIT_SPEC_tower_frames_v2.md': '133e8cfdbb149401767c76fc5908154b9dd106d2a4b580bcca81d207615169aa',
    'KIT_SPEC_object_route_r0dev_v2.md': '640e8deb8fe7d661abbeb3bb0d345aeb2b6eda4f50af346f0f16b0cf4788cce3',
    'REVIEW_RESPONSE_harev.md': '7b290d26faf03639bb5a9d4e1c418ace7f79534ae2a52a5f0fa4133fcdb39941',
}
texts, checks = {}, {}
for name, expected in pins.items():
    path = ROOT / 'inputs' / name
    texts[name] = read(path)
    actual = INPUTS[str(path)]['sha256']
    checks[name] = {'expected': expected, 'actual': actual, 'matches': expected == actual}
assert all(x['matches'] for x in checks.values()), 'A mismatched pin voids that file review.'
read(ROOT / 'inputs/BINDING_RULINGS.txt')
result('full snapshot pins', 'VERIFIED', checks, list(pins),
       'SHA256 of the once-copied local bytes, compared with the full task pins.')
response = texts['REVIEW_RESPONSE_harev.md']
assert all(pin in response for name, pin in pins.items() if name != 'REVIEW_RESPONSE_harev.md')

# Use the exact sequential admission loop from v2; update only the new estimates.
steps = [('tower_A', .5, .75), ('tower_B', 2.5, 3), ('K1_track', 1.3, 1.75),
         ('R0_base', 3, 3.5), ('R0_track', 3, 3.25), ('R0_94', 3.5, 4),
         ('camera_C', .6, .75), ('devS1', 2, 2), ('devS1_track', 1, 1)]
scenarios = {}
budget_loop = next(n for n in v2_ast.body if isinstance(n, ast.For)
                   and isinstance(n.target, ast.Name) and n.target.id == 'mode')
exec(compile(ast.Module(body=[budget_loop], type_ignores=[]), str(V2 / 'recompute.py'), 'exec'), globals())
budget = dict(parts=[dict(name=n, estimate=e, stop=s) for n,e,s in steps],
              base_expected=round(sum(e for n,e,s in steps if n not in ['R0_track','R0_94','devS1_track']), 3),
              all_expected=round(sum(e for n,e,s in steps), 3),
              all_stops=round(sum(s for n,e,s in steps), 3), scenarios=scenarios,
              scenario_scope='Capacity arithmetic only, not executable schedules; dependent diagnostics cannot run without prerequisite outputs.',
              reader_reads='OUTSIDE AUTHORIZATION; separate budget required',
              gpu_hours_used_by_this_review=0)
assert (budget['base_expected'], budget['all_expected'], budget['all_stops']) == (9.9,17.4,20.0)
assert all(s['used'] <= 16 for s in scenarios.values())
result('revised GPU ledger arithmetic', 'VERIFIED', budget, ['T:54', 'O:42'],
       'Reuse v2 sequential admission loop with T:54 estimates/stops; one card per simulated part. Concurrent launches must also reserve running stops. Estimates are not measured runtimes.')

result('new missing-table rule algebra', 'DERIVED, CONDITIONAL',
       dict(train_table_rows=883, missing_table_rows='m, not measured',
            optimistic_shift_type_points='100 * sum(A0 scores on missing-table rows) / 883',
            upper_bound_type_points='100 * m / 883'), ['B:33', 'B:90'],
       'On a missing-table row a refusing candidate should score 0 against the available A0 score b; zeroing both changes its paired difference from -b to 0. No missing-table count is assumed.')
result('decision thresholds and prospective costs', 'SPECIFIED, NOT MEASURED',
       dict(box_type_points=3, size_type_points=5, relative_distance_type_points=3,
            appearance_order_type_points=5, size_treatment_lower_bound=-2,
            selector_cpu_cost='minutes per retrain (B:64), unmeasured',
            size_gate_replay_extra_gpu_hours=0,
            table_comparator_repair_extra_gpu_hours=0,
            gate_replay_delay='CPU runtime unmeasured; after selected train construction exists'),
       ['B:64,87,90,91', 'O:52,57-59'],
       'Transcribe predeclared bars; CPU-only fixes reuse kit outputs. No accuracy gain or wall-clock duration is inferred.')

result('prior evidence provenance', 'INHERITED, NOT RERUN',
       dict(command=prior['command'], input_sha256=prior['inputs'],
            prior_review_code=prior['review_code'],
            retained_findings='Only the ten requested open findings were reassessed; no raw metrics are claimed as newly recomputed.'),
       [str(V2 / 'RECOMPUTE.json')],
       'Hash and retain the prior evidence manifest and original command; do not reopen raw data or consume evaluation looks.')

report = ROOT / 'out/REVIEW_VERDICT.md'
report_text = read(report)
assert len(report_text.splitlines()) <= 50
requested = [1,6,8,13,14,16,17,15,18,19]
for number in requested:
    assert f'| #{number} | CLOSED |' in report_text
for number in [20,21,22]:
    assert f'| NEW #{number} — OPEN |' in report_text
read(Path(__file__).resolve())
output = dict(command=CMD, inputs=INPUTS, results=RESULTS,
              report_lines=len(report_text.splitlines()), requested_findings=requested,
              verdict='ACCEPT WITH FINDINGS')
(ROOT / 'out/RECOMPUTE.json').write_text(json.dumps(output, indent=2, allow_nan=False)+'\n')
print(json.dumps(dict(pin_matches=len(checks), report_lines=output['report_lines'],
                     budget=budget, verdict=output['verdict']), indent=2))
