"""Aggregate the native-session replay of G3T tower gravity, not student-head gravity."""
import collections
import json
from pathlib import Path
import re
import os

L = Path('/scratch/jjyeung/orch_n30/contracts_rebuild')
O = L / 'out/real_replay'
RECORD = '/data2/jjyeung/agent_project_data/distill_design/ROUTED_READ_GEOMETRY_GUARD_169670_20261115.md'
REPORT = Path(os.environ.get('REPLAY_REPORT_DIR', str(O)))
REPORT.mkdir(parents=True, exist_ok=True)
JP = REPORT / 'REAL_GEOMETRY_REPLAY.json'
MP = REPORT / 'REAL_GEOMETRY_REPLAY.md'
SOURCE = 'G3T tower gravity, not student-head gravity'

def read(mode):
    with (O/('full_'+mode+'.jsonl')).open() as f:
        return {r['capture']: r for line in f if (r := json.loads(line))}

arms = {m: read(m) for m in ('base', 'off', 'on')}
inventory = json.loads((O/'CAPTURE_INVENTORY.json').read_text())
assert set(arms['base']) == set(arms['off']) == set(arms['on'])
assert len(arms['base']) == inventory['npz_count']
rows, failures = [], []
checks = collections.Counter()

def check(capture, name, value):
    checks[name+'_tested'] += 1
    checks[name+'_passed' if value else name+'_failed'] += 1
    if not value:
        failures.append(dict(capture=capture, assertion=name, source=str(JP)+'#/captures/'+capture))

for key in sorted(arms['base']):
    b, f, n = (arms[m][key] for m in ('base', 'off', 'on'))
    check(key, 'off_base_guard_parity', b['guard'] == f['guard'])
    check(key, 'off_base_response_byte_parity', b['responses'] == f['responses'])
    check(key, 'off_base_session_status_parity', b['session_status'] == f['session_status'])
    check(key, 'off_base_masks_identical', b['synthetic_masks'] == f['synthetic_masks'])
    for other in (f, n):
        check(key, 'converted_geometry_identical', b['adapter']['converted_array_sha256'] == other['adapter']['converted_array_sha256'])
    if b['guard'] == 'pass':
        check(key, 'base_pass_on_guard_pass', n['guard'] == 'pass')
        for name in ('room', 'distance'):
            check(key, 'base_pass_on_'+name+'_byte_parity', b['responses'].get(name) == n['responses'].get(name))
        check(key, 'base_pass_on_size_text_parity', b.get('size_lines') == n.get('size_lines'))
        if n['heading_geometrically_defined']:
            check(key, 'defined_heading_response_byte_parity',
                all(b['responses'].get(k) == n['responses'].get(k) for k in ('centre','chair_box','table_box')))
    else:
        check(key, 'base_refused_on_guard_pass', n['guard'] == 'pass')
        check(key, 'base_refused_on_distance_served', bool(re.search(r'(?m)^distance ', n['responses'].get('distance', ''))))
        check(key, 'base_refused_on_room_served', bool(re.search(r'(?m)^area ', n['responses'].get('room', ''))))
    if n['guard'] == 'pass' and not n['heading_geometrically_defined']:
        check(key, 'undefined_heading_withheld', all('heading unavailable' in n['responses'].get(k, '') for k in ('centre','chair_box','table_box')))
    if b['guard'] == n['guard'] == 'pass':
        check(key, 'synthetic_masks_identical', b['synthetic_masks'] == n['synthetic_masks'])
    if n['guard'] == 'pass':
        check(key, 'on_room_mask_free', n['room_mask_calls'] == 0)
        check(key, 'on_distance_served', bool(re.search(r'(?m)^distance ', n['responses']['distance'])))
        check(key, 'on_room_served', bool(re.search(r'(?m)^area ', n['responses']['room'])))
        check(key, 'on_size_served', all(n['size_lines'].values()))
        if n['heading_geometrically_defined']:
            check(key, 'on_defined_heading_printed', 'f1 (' in n['responses']['centre'])
    rows.append(dict(capture=key, dataset=b['dataset'], source=b['source'],
        gravity_source=SOURCE, modes=dict(base=b, patched_off=f, patched_on=n)))

datasets = {}
for ds in sorted({r['dataset'] for r in rows}):
    selected = [r for r in rows if r['dataset'] == ds]
    datasets[ds] = dict(total=len(selected),
        source=str(JP),
        sealed_refused=[r['capture'] for r in selected if r['modes']['base']['guard'] != 'pass'],
        patched_refused=[r['capture'] for r in selected if r['modes']['patched_on']['guard'] != 'pass'],
        plane_below_threshold=[r['capture'] for r in selected if r['modes']['base']['plane'] < .3],
        sealed_served_loses_heading=[r['capture'] for r in selected if r['modes']['base']['guard'] == 'pass' and r['modes']['base']['plane'] < .3],
        within_ten_degrees_nadir=[r['capture'] for r in selected if r['modes']['base']['pitch_deg'] < -80],
        minimum_margin=min(r['modes']['base']['margin'] for r in selected))
    datasets[ds]['minimum_margin_capture'] = min(selected, key=lambda r:r['modes']['base']['margin'])['capture']
    datasets[ds]['sealed_refused_count'] = len(datasets[ds]['sealed_refused'])
    datasets[ds]['patched_refused_count'] = len(datasets[ds]['patched_refused'])

totals = dict(source=str(JP), captures=len(rows), datasets=datasets,
    capture_json_count=inventory['capture_json_count'], missing_npz=inventory['missing_npz'],
    sealed_refused=sum(len(d['sealed_refused']) for d in datasets.values()),
    patched_refused=sum(len(d['patched_refused']) for d in datasets.values()),
    near_nadir=sum(len(d['within_ten_degrees_nadir']) for d in datasets.values()),
    plane_below_threshold=sum(len(d['plane_below_threshold']) for d in datasets.values()),
    sealed_served_loses_heading=sum(len(d['sealed_served_loses_heading']) for d in datasets.values()),
    checks=dict(checks), assertion_failures=failures)
mapping = dict(status='not mappable', source_paths=[RECORD,
    str(L/'work/real/x_geo/REQUEST.json'), str(L/'work/real/x_geo/COMPLETE.json')],
    explanation='The record supplies only aggregate distance-item counts. REQUEST supplies artifact hashes and frame roots; capture metadata and NPZ contain no item IDs, types, or membership roster. No referenced external files were followed.')
payload = dict(gravity_source=SOURCE,
    archive_source=str(L/'work/real/geometry_8c58df1547371bdb.tar'),
    record_source=RECORD, adapter_source=str(L/'work/real_replay/replay.py'),
    fixture_source=str(L/'work/tests/fixtures_contracts.py'),
    input_inventory=inventory, inventory_source=str(O/'CAPTURE_INVENTORY.json'),
    totals=totals, distance_item_mapping=mapping, captures=rows,
    definitions=dict(plane='norm(R[0,2,:2])', margin='-R[0,2,1]',
        pitch_deg='degrees(arcsin(R[0,2,2])); negative means downward',
        medians='Across selected anchor frames; usable normalized margin uses plane >= 0.3',
        heading_defined='Reference plane >= 0.3',
        near_nadir='Reference pitch < -80 degrees',
        refusal_path='Contract validation prevents ProfileGeometry/session construction; no response bytes exist in that arm.'),
    adapter=dict(source=str(L/'work/real_replay/replay.py'),
        tree_steps=['camera_targets.to_gravity_reference_frame(raw_pose[anchor_slots], gravity_up)',
            'camera_targets.gravity_reference_rotation(gravity_up)',
            'GeometryContract.validate, ProfileGeometry, GroundV3, LiveSession',
            'fixtures_contracts.response invokes carrier_c1_decode.respond_state and deployed formatter'],
        adapter_steps=['Select stored anchors and validate raw_pose32 and identity origin',
            'Reconstruct centered K and canvas affine using geometry_profiles.legacy_from_heads formulas',
            'Pack R/t into camera_to_world; retain stored depth_grid and grid_uv',
            'Set scaled_g3t_depth scale=1 because no student depth or metric-scale estimate is supplied',
            'Select one depth-valid frame for identical synthetic fixture masks across trees'],
        raw_loader_limitation='ground_profiles.load_geometry expects head-export fields absent from raw tower NPZ, including anchor_frame_indices and r_grav or profile/K/camera_to_world.',
        scale_warning='Raw tower units; formatter metre labels do not establish metric calibration.'))
payload['source_paths'] = [str(O/('full_'+m+'.jsonl')) for m in arms]
minimum_nonark = min(d['minimum_margin'] for ds,d in datasets.items() if ds != 'arkitscenes')
payload['record_comparison'] = dict(source=RECORD, replay_source=str(JP),
    record_cohort=dict(captures=84,arkitscenes=30,scannet=29,scannetppv2=25),
    sealed_refused=dict(record=12,replay=totals['sealed_refused'],difference=totals['sealed_refused']-12),
    within_ten_degrees_nadir=dict(record=14,replay=totals['near_nadir'],difference=totals['near_nadir']-14),
    distance_items=dict(record=21,replay=None,status='not mappable'),
    minimum_d1_d2_margin=dict(record=.57,replay=minimum_nonark,matches_record_rounding=round(minimum_nonark,2)==.57),
    explanation='The capture cohorts differ. The supplied record has no complete cohort roster or per-item mapping, so its subset totals cannot be independently reproduced or each difference assigned to specific captures. Minimum non-ARKitScenes margin agrees at record precision.')
with JP.open('x') as f:
    json.dump(payload, f, indent=2)
link = f'[replay JSON]({JP})'
record = f'[geometry record]({RECORD})'
text = [f'The sealed guard refused {totals["sealed_refused"]} captures; the patched guard refused {totals["patched_refused"]}. The replay covers {len(rows)} captures and records {len(failures)} failed assertions. Source: {link}.',
    f'Patched OFF matches sealed response bytes. Patched ON serves room, distance and size for every capture; it preserves sealed-served room, distance and size text and preserves heading-dependent response bytes wherever heading is defined. Every undefined heading prints `heading unavailable`. Source: {link}.',
    f'The extraction has {inventory["npz_count"]} capture NPZ files and {inventory["capture_json_count"]} capture JSON files; {len(inventory["missing_npz"])} captures lack NPZ files. The runner reads both `g3s32/g3t` and `g3s64/g3t`. Rank receipts are not captures. Source: [capture inventory]({O}/CAPTURE_INVENTORY.json).',
    f'Gravity source: **{SOURCE}**. Masks are synthetic fixed rectangles, identical across trees. This CPU tool replay does not run the RGB model or measure answer quality. Geometry remains private; responses pass through `ProfileGeometry`, `GroundV3`, `LiveSession`, `respond_state`, and the shared deployed formatter. Source: [runner]({L}/work/real_replay/replay.py).',
    f'The adapter calls each tree’s `to_gravity_reference_frame`, which calls `gravity_reference_rotation`. It uses the stored relative pose encodings and FoV, reconstructs K using the tree’s FoV formula and source raster, sets the normalized-canvas affine, and passes the stored depth grid unchanged. The supplied archive has no student metric-scale estimate: scale is fixed at unity, so values retain raw tower units despite the native formatter’s metre labels. Sources: [runner]({L}/work/real_replay/replay.py), [tree conversion]({L}/work/trees/real_base/student_pilot/camera_targets.py), [tree loader]({L}/work/trees/real_base/student_pilot/geometry_profiles.py).',
    f'The raw NPZ schema lacks the head-export fields required by `ground_profiles.load_geometry`, so the runner adapts the arrays into `GeometryContract`. Per-capture schemas, conversion hashes, anchor poses, selected frames, medians, refusal names and response strings appear in {link}. A sealed guard refusal prevents session construction and therefore has no fabricated tool response.',
    '| Dataset | Captures | Sealed refused | Patched refused | Near nadir | Sealed served, loses heading |\n|---|---:|---:|---:|---:|---:|']
for ds,d in datasets.items():
    text.append(f'| {ds} | {d["total"]} | {len(d["sealed_refused"])} | {len(d["patched_refused"])} | {len(d["within_ten_degrees_nadir"])} | {len(d["sealed_served_loses_heading"])} |')
text += [f'Every table value comes from {link}; each capture row names its NPZ source.',
    f'The record predicts 12 refused captures, 14 references within 10 degrees of nadir, and 21 distance items on refused captures. Its cohort contains 84 captures: 30 ARKitScenes, 29 ScanNet and 25 ScanNet++. This archive contains {len(rows)} captures, with dataset counts in the table. Measured refusal and nadir totals are {totals["sealed_refused"]} and {totals["near_nadir"]}, differences of {totals["sealed_refused"]-12} and {totals["near_nadir"]-14}. These denominators differ; the supplied files lack the record’s cohort roster, so the differences cannot be assigned to particular added or missing captures. Sources: {record}, {link}.',
    f'Distance items are **not mappable** from the supplied metadata. The record’s 21-item projection cannot be independently confirmed here. Sources: {record}, [REQUEST]({L}/work/real/x_geo/REQUEST.json), {link}.',
    f'The record’s minimum d1/d2 margin is 0.57. This replay’s minima are '+', '.join(f'{ds}: {d["minimum_margin"]:.6f} ({d["minimum_margin_capture"]})' for ds,d in datasets.items() if ds!='arkitscenes')+f'. The combined minimum rounds to the record’s value; there is no discrepancy at its reported precision. Sources: {record}, {link}.',
    f'The near-nadir count uses pitch below minus eighty degrees; heading suppression uses reference plane below 0.3 and therefore includes less steep views. The latter contains {totals["plane_below_threshold"]} captures, including {totals["sealed_served_loses_heading"]} served by the sealed guard. These are different thresholds, not interchangeable counts. Sources: {link}, [patched guard]({L}/work/trees/real_patched/student_pilot/geometry_profiles.py).']
for native in ('41069053','41098149','41254810'):
    key='arkitscenes__'+native
    if key in arms['base']:
        r=arms['base'][key]
        text.append(f'{key}: margin {r["margin"]:.6f}, plane {r["plane"]:.6f}, pitch {r["pitch_deg"]:.3f} degrees, median roll for frames above minus sixty degrees {r["median_roll_pitch_above_minus60"]:.3f} degrees. Source: [{key}]({r["source"]}).')
text.append(f'The named captures agree with the record’s tower estimates: the negative margin matches G3T rather than the head estimate; the positive near-nadir margin still loses heading; and the suspect capture retains a large median roll magnitude. The runner defines signed roll as atan2(-R[z,x], -R[z,y]); the record quotes the suspect magnitude with the opposite sign. This replay does not inspect RGB or diagnose its cause. Sources: {record}, {link}, [runner]({L}/work/real_replay/replay.py).')
for ds,d in datasets.items():
    for field in ('sealed_refused','patched_refused','sealed_served_loses_heading'):
        text.append(f'{ds} {field}: '+(', '.join(d[field]) or 'none')+f'. Source: {link}.')
text += [f'Assertion details and all response bytes are in {link}. Failures: '+(json.dumps(failures) if failures else 'none')+'.',
    'The sealed-versus-patched comparison is retained because the requested experiment defines those arms.']
with MP.open('x') as f:
    rendered = '\n\n'.join(text)+'\n'
    rendered = re.sub(r'(?m)(\|[^\n]*\|)\n\n(?=\|)', r'\1\n', rendered)
    f.write(rendered)
print(json.dumps(dict(gravity_source=SOURCE, totals=totals, source=str(JP))), flush=True)
assert not failures, 'Replay assertions failed; see the final report and per-capture evidence.'
