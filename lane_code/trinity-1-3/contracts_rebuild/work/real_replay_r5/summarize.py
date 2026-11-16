"""Aggregate the native-session replay of G3T tower gravity, not student-head gravity."""
import collections
import json
from pathlib import Path
import re
import os

L = Path('/scratch/jjyeung/orch_n30/contracts_rebuild')
O = L / 'out/real_replay_r5'
RECORD = '/data2/jjyeung/agent_project_data/distill_design/ROUTED_READ_GEOMETRY_GUARD_169670_20261115.md'
REPORT = Path(os.environ.get('REPLAY_REPORT_DIR', str(O)))
REPORT.mkdir(parents=True, exist_ok=True)
JP = REPORT / 'REAL_GEOMETRY_REPLAY.json'
MP = REPORT / 'REAL_GEOMETRY_REPLAY.md'
SOURCE = 'G3T tower gravity, not student-head gravity'

def read(mode):
    with (O/('closed_r5_'+mode+'.jsonl')).open() as f:
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
        for name in ('room', 'distance', 'camera_gap'):
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
    if n['guard'] == 'pass':
        for name in ('move', 'turn'):
            check(key, 'relative_'+name+'_served', 'heading unavailable' not in n['responses'][name] and 'error:' not in n['responses'][name])
            check(key, 'relative_'+name+'_defined_computation_byte_parity', n['responses'][name] == n['heading_defined_computation'][name])
        check(key, 'count_served', n['responses']['count'].startswith('chair: 1 found'))
        check(key, 'camera_gap_served', n['responses']['camera_gap'].startswith('distance '))
        check(key, 'depth_camera_and_spread_served', 'cam' in n['responses']['depth'] and 'spread ' in n['responses']['depth'])
        angle = n['responses']['angle']; expected = n['heading_defined_computation']['angle']
        check(key, 'angle_scalar_or_same_defined_refusal',
            angle.split('; dot ')[-1] == expected.split('; dot ')[-1] and
            ('theta ' in angle or angle == expected and angle.startswith('error:')))
        if not n['heading_geometrically_defined']:
            check(key, 'pose_heading_fields_withheld', 'yaw heading unavailable' in n['responses']['pose'])
            check(key, 'centre_camera_and_spread_served', 'cam' in n['responses']['centre'] and 'spread ' in n['responses']['centre'])
            check(key, 'box_support_served', all('frames ' in n['responses'][name] for name in ('chair_box','table_box')))
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
    record_source=RECORD, adapter_source=str(L/'work/real_replay_r5/replay.py'),
    fixture_source=str(L/'work/tests_r5/fixtures_contracts.py'),
    input_inventory=inventory, inventory_source=str(O/'CAPTURE_INVENTORY.json'),
    totals=totals, distance_item_mapping=mapping, captures=rows,
    definitions=dict(plane='norm(R[0,2,:2])', margin='-R[0,2,1]',
        pitch_deg='degrees(arcsin(R[0,2,2])); negative means downward',
        medians='Across selected anchor frames; usable normalized margin uses plane >= 0.3',
        heading_defined='Reference plane >= 0.3',
        near_nadir='Reference pitch < -80 degrees',
        refusal_path='Contract validation prevents ProfileGeometry/session construction; no response bytes exist in that arm.'),
    adapter=dict(source=str(L/'work/real_replay_r5/replay.py'),
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
payload['source_paths'] = [str(O/('closed_r5_'+m+'.jsonl')) for m in arms]
minimum_nonark = min(d['minimum_margin'] for ds,d in datasets.items() if ds != 'arkitscenes')
payload['record_comparison'] = dict(source=RECORD, replay_source=str(JP),
    record_cohort=dict(captures=84,arkitscenes=30,scannet=29,scannetppv2=25),
    sealed_refused=dict(record=12,replay=totals['sealed_refused'],difference=totals['sealed_refused']-12),
    within_ten_degrees_nadir=dict(record=14,replay=totals['near_nadir'],difference=totals['near_nadir']-14),
    distance_items=dict(record=21,replay=None,status='not mappable'),
    minimum_d1_d2_margin=dict(record=.57,replay=minimum_nonark,matches_record_rounding=round(minimum_nonark,2)==.57),
    explanation='The capture cohorts differ. The supplied record has no complete cohort roster or per-item mapping, so its subset totals cannot be independently reproduced or each difference assigned to specific captures. Minimum non-ARKitScenes margin agrees at record precision.')
near = [r for r in rows if r['dataset']=='arkitscenes' and r['modes']['patched_on']['plane'] < .3]
for row in near:
    n=row['modes']['patched_on']
    row['heading_field_audit'] = dict(
        served=['move dx/dy/dz/distance', 'relative turn', 'depth camera coordinates and spread',
                'pose height', 'ground camera coordinates, height, spread, support and size',
                'box support, height and size', 'instance count and camera coordinates', 'room fields', 'box and camera distances'],
        withheld=['depth and ground f1 horizontal components', 'pose f1 horizontal components and yaw',
                  'box f1 horizontal centre and yaw'],
        angle=n['responses']['angle'], relative_frames=n['relative_frames'],
        source=row['source'])
    audit=row['heading_field_audit']
    audit['independent_refusals']=[]
    if n['responses']['angle'].startswith('error:'):
        audit['independent_refusals'].append(n['responses']['angle'])
    else:
        audit['served'].append('angle dot, cross, theta and category')
        if 'u heading unavailable' in n['responses']['angle']:
            audit['withheld'].append('calculator u/v horizontal components')
payload['totals']['near_reference_move_turn_served'] = sum(
    all('heading unavailable' not in r['modes']['patched_on']['responses'][name] and
        'error:' not in r['modes']['patched_on']['responses'][name] for name in ('move','turn')) for r in near)
payload['totals']['angle_defined_refusals'] = [r['capture'] for r in rows if r['modes']['patched_on']['responses'].get('angle','').startswith('error:')]
with JP.open('w') as f:
    json.dump(payload, f, separators=(",", ":"))
link=f'[replay JSON]({JP})'
text=[f"The ON guard serves {len(rows)} captures; the sealed guard refuses {totals['sealed_refused']}. OFF equals the sealed response bytes for every capture. Assertions failed: {len(failures)}. Source: {link}.",
    f"The reference plane is below the default heading threshold for {len(near)} ARKitScenes captures. Every one serves move and turn between the recorded nonreference frames, depth camera coordinates, centre camera coordinates, vertical coordinates, support, size, room measurements, and distance. Only reference-heading fields are withheld. The {totals['sealed_served_loses_heading']} ARKitScenes captures served by the sealed guard lose only their frame-1-heading fields. Source: {link}.",
    f"Calculator scalars match the defined-heading computation. Existing geometric or rounding refusals, if any, are listed under angle_defined_refusals in {link}; they are not heading refusals.",
    f"Gravity comes from the G3T tower. The replay uses fixed synthetic masks and does not run the RGB model. The archive has no metric-scale estimate, so native metre labels carry raw tower units. Source: [runner]({L}/work/real_replay_r5/replay.py).",
    '| Dataset | Captures | Sealed refused | ON refused | Reference plane below threshold | Sealed served with undefined reference heading |\n|---|---:|---:|---:|---:|---:|']
for ds,d in datasets.items():
    text.append(f"| {ds} | {d['total']} | {len(d['sealed_refused'])} | {len(d['patched_refused'])} | {len(d['plane_below_threshold'])} | {len(d['sealed_served_loses_heading'])} |")
text += [f'All table values: {link}. Each capture includes its NPZ path, conversion hashes, actual call strings, endpoint frames, and base/ON/OFF response bytes.',
    'Per-capture field availability follows. The full field classification and math are in [HEADING_DEPENDENCE_R4.md]('+str(L/'out/HEADING_DEPENDENCE_R4.md')+').',
    '| Capture/source | Relative frames | Served | Withheld for reference heading | Independent calculator refusal |\n|---|---|---|---|---|']
for r in near:
    a=r['heading_field_audit']
    text.append(f"| [{r['capture']}]({r['source']}) | {a['relative_frames']} | "+'; '.join(a['served'])+' | '+'; '.join(a['withheld'])+' | '+('; '.join(a['independent_refusals']) or 'none')+' |')
text.append(f'Failed assertions: {failures}. Source: {link}.')
with MP.open('w') as f:
    rendered='\n\n'.join(text)+'\n'
    rendered=re.sub(r'(?m)(\|[^\n]*\|)\n\n(?=\|)',r'\1\n',rendered)
    f.write(rendered)
print(json.dumps(dict(captures=len(rows),failures=failures,source=str(JP))),flush=True)
assert not failures, 'Replay assertions failed; inspect the per-capture evidence.'
