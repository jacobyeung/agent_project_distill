import argparse
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path, PurePosixPath
import re
import statistics

import numpy as np
from scipy.spatial import Delaunay

from .blocking import scene_key
from .formats import UNIT_METERS
from .geometry import room_area
from .io import canonical, pin, read_json, read_jsonl, source_commit, verify_pin
from .mesh_membership import instance_faces
from .swarm import require, write_new


AREA_UNITS = re.compile(r'\b(square meters|square feet)\b')


def scene_identity(dataset, scene):
    dataset = {'scannetppv2': 'scannetpp', 'scannetpp_v2': 'scannetpp'}.get(dataset, dataset)
    return dataset, scene


def area_label(answer, question):
    units = set(AREA_UNITS.findall(question))
    if len(units) != 1:
        raise ValueError('Room answer needs exactly one explicit area unit')
    unit = units.pop()
    value = Decimal(str(answer).strip())
    if not value.is_finite() or value <= 0:
        raise ValueError('Room area must be finite and positive')
    return {'answer': str(answer), 'units': unit, 'area_m2': float(value * UNIT_METERS[unit])}


def reference_summary(labels):
    if not labels:
        return None
    preferred = [row['area_m2'] for row in labels if row['units'] == 'square meters']
    values = [row['area_m2'] for row in labels]
    center = statistics.median(preferred or values)
    conflict = max(values) - min(values) > max(0.25, 0.02 * center)
    return {'area_m2': None if conflict else center, 'label_count': len(labels),
            'minimum_m2': min(values), 'maximum_m2': max(values),
            'conflicting_labels': conflict, 'labels': labels}


def alpha_areas(points_xy, radius_limits=(0.3, 0.6, 1.0, 2.0), grid_m=0.02):
    points = np.asarray(points_xy, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all() or grid_m <= 0:
        raise ValueError('Expected finite XY points and a positive projection grid')
    sampled = np.unique(np.round(points / grid_m) * grid_m, axis=0)
    if len(sampled) < 3 or len(sampled) > 1000000:
        raise ValueError('Diagnostic XY point count is outside the bounded audit range')
    triangles = sampled[Delaunay(sampled).simplices]
    u, v = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    areas = np.abs(u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]) / 2
    product = np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1) * np.linalg.norm(u - v, axis=1)
    radius = np.divide(product, 4 * areas, out=np.full(len(areas), np.inf), where=areas > 0)
    return {'by_circumradius_cutoff_m': {str(bound): float(areas[radius <= bound].sum()) for bound in radius_limits},
            'convex_hull_m2': float(areas.sum()), 'raw_point_count': len(points),
            'projection_point_count': len(sampled), 'projection_grid_m': grid_m,
            'is_official_benchmark_ground_truth': False,
            'scope': 'Full source-mesh XY alpha-shape sensitivity check; benchmark alpha and preprocessing are not published in the cited definition.'}


def geometry_audit(row):
    provenance = row['provenance']
    receipt = read_json(verify_pin(provenance['scene_receipt']))
    require(receipt['gravity_up'] == [0, 0, 1]
            and receipt['coordinate_frame'] == 'source_world_meters_opencv_camera_to_world', 'room_geometry_frame')
    assets = provenance['assets']
    require(receipt['instance_mesh']['sha256'] == assets['instance_mesh']['sha256'], 'room_geometry_receipt_binding')
    mesh_path = verify_pin(assets['instance_mesh'])
    groups = read_json(verify_pin(assets['instances']))['segGroups']
    labels = {int(group.get('objectId', group.get('id'))): group['label'].lower().strip() for group in groups}
    with np.load(mesh_path, allow_pickle=False) as stored:
        mesh = {name: stored[name] for name in stored.files}
    if 'face_instance_ids' in mesh:
        mesh['instance_ids'] = mesh['face_instance_ids']
    vertices, faces = mesh['vertices_world'], mesh['faces']
    require(vertices.ndim == 2 and vertices.shape[1] == 3 and np.isfinite(vertices).all()
            and faces.ndim == 2 and faces.shape[1] == 3 and np.all(faces >= 0) and np.all(faces < len(vertices)),
            'room_geometry_shapes')
    ids = row['ground_truth']['measurements'][0]['object_ids']
    require(ids and all(labels[iid] == 'floor' for iid in ids), 'room_floor_labels')
    floor_objects = [{'label': 'floor', 'triangles': vertices[faces[instance_faces(mesh, iid)]].astype(np.float64)} for iid in ids]
    replayed = room_area(floor_objects)
    expected = row['ground_truth']['measurements'][0]['value_si']
    require(np.isclose(replayed, expected, rtol=1e-7, atol=1e-8), 'room_floor_replay')
    return {'floor_triangle_union_m2': replayed, 'floor_replay_matches_stored_measurement': True,
            'floor_triangles': sum(len(obj['triangles']) for obj in floor_objects),
            'all_scene_vertices': len(vertices), 'all_scene_faces': len(faces),
            'full_scene_alpha': alpha_areas(vertices[:, :2]),
            'pins': [provenance['scene_receipt'], assets['instance_mesh'], assets['instances']]}


def published_labels(conventions, wanted):
    vsi_spec, benchmark_spec = conventions['authorities']['vsi'], conventions['authorities']['vsibench']
    vsi_path, benchmark_path = verify_pin(vsi_spec), verify_pin(benchmark_spec)
    upstream, benchmark, invalid = defaultdict(list), defaultdict(list), []
    count = 0
    for number, row in enumerate(read_jsonl(vsi_path), 1):
        count = number
        if row.get('question_type') != 'absolute_size_room' or not isinstance(row.get('video'), str):
            continue
        video = PurePosixPath(row['video'])
        key = scene_identity(video.parent.name, video.stem)
        if key not in wanted:
            continue
        human = [turn['value'] for turn in row['conversations'] if turn['from'] == 'human']
        answers = [turn['value'] for turn in row['conversations'] if turn['from'] == 'gpt']
        require(len(human) == len(answers) == 1, 'room_reference_conversation')
        try:
            label = area_label(answers[0], human[0])
        except ValueError as error:
            invalid.append({'line': number, 'video': row['video'], 'reason': str(error)})
            continue
        upstream[key].append({**label, 'source_line': number, 'video': row['video'], 'question': human[0]})
    benchmark_groups = set()
    for row in read_json(benchmark_path):
        benchmark_groups.add(scene_key(row['dataset'], row['scene_name']))
        if row['question_type'] != 'room_size_estimation':
            continue
        key = scene_identity(row['dataset'], row['scene_name'])
        if key in wanted:
            label = area_label(row['ground_truth'], row['question'])
            benchmark[key].append({**label, 'id': row['id'], 'question': row['question'], 'pruned': row.get('pruned')})
    return upstream, benchmark, benchmark_groups, {'vsi_source_rows_streamed': count, 'invalid_matching_labels': invalid,
                                                'source_pins': [vsi_spec, benchmark_spec]}


def audit(common_done, conventions_path, limit=20, geometry=True):
    commit = source_commit()
    done = read_json(common_done)
    require(done.get('passed') is True and done['rows'] == 1000, 'room_common_admission')
    membership = read_json(verify_pin(done['membership']))
    index_pin = membership['candidate_indices']['a0']
    entries = list(read_jsonl(verify_pin(index_pin)))
    by_id = {entry['qid']: entry for entry in entries}
    require(len(by_id) == len(entries) == 1000, 'room_common_index_census')
    rooms = [row for row in membership['rows'] if row['family'] == 'gtm_room_size']
    require(len(rooms) == 100 and 20 <= limit <= len(rooms), 'room_fixed_selection_size')
    wanted = {scene_identity(row['dataset'], row['scene']) for row in rooms}
    conventions = read_json(conventions_path)
    require(conventions['measurements']['gtm_room_size']['formula']
            == 'planar polygon union; preserve concavities and holes; never fill unobserved floor', 'room_gtm_convention')
    upstream, benchmark, benchmark_groups, source_audit = published_labels(conventions, wanted)
    output, cache = [], {}
    for position, selected in enumerate(rooms[:limit], 1):
        entry = by_id[selected['qid']]
        row_pin = {'path': entry['row_path'], 'sha256': entry['row_sha256']}
        row = read_json(verify_pin(row_pin))
        target_pin = {'path': entry['target_path'], 'sha256': entry['sha256']}
        target = verify_pin(target_pin).read_text().strip()
        require(row['qid'] == selected['qid'] and row['dataset'] == selected['dataset']
                and row['scene'] == selected['scene'] and str(row['ground_truth']['answer']) == str(selected['answer'])
                and target == str(selected['answer']), 'room_common_source_identity')
        question = row['student_input']['question']
        label = area_label(selected['answer'], question)
        require(label['units'] == row['ground_truth']['units'], 'room_target_unit')
        key = scene_identity(row['dataset'], row['scene'])
        exact = reference_summary(benchmark[key])
        training_reference = reference_summary(upstream[key])
        reference = exact or training_reference
        reference_area = reference['area_m2'] if reference else None
        record = {'qid': row['qid'], 'dataset': row['dataset'], 'scene': row['scene'],
                  'question': question, 'target_answer': str(selected['answer']), 'target_units': label['units'],
                  'target_m2': label['area_m2'], 'stored_gtm_m2': row['ground_truth']['measurements'][0]['value_si'],
                  'observations': row['observations'], 'row_pin': row_pin, 'target_pin': target_pin,
                  'vsibench_same_scene_reference': exact, 'vsi590k_same_scene_reference': training_reference,
                  'reference_kind': 'VSIBench same-scene ground truth' if exact else 'VSI-590K published train-scene area' if training_reference else 'unavailable',
                  'reference_m2': reference_area,
                  'target_to_published_reference_ratio': label['area_m2'] / reference_area if reference_area else None}
        if geometry:
            if key not in cache:
                cache[key] = geometry_audit(row)
            record['geometry'] = cache[key]
            require(np.isclose(cache[key]['floor_triangle_union_m2'], record['stored_gtm_m2'], rtol=1e-7, atol=1e-8),
                    'room_repeat_scene_measurement')
        output.append(record)
        print(canonical({'checked_room_row': position, 'qid': row['qid'], 'target_m2': label['area_m2'],
                         'reference_m2': reference_area, 'ratio': record['target_to_published_reference_ratio']}), flush=True)
    ratios = [row['target_to_published_reference_ratio'] for row in output if row['target_to_published_reference_ratio'] is not None]
    return {'schema': 'h05-room-convention-audit-v1', 'checked_at': datetime.now(timezone.utc).isoformat(),
            'commit': commit, 'audit_source': pin(__file__), 'common_done': pin(common_done),
            'membership': done['membership'], 'a0_index': index_pin, 'conventions': pin(conventions_path),
            'official_benchmark_definition': {'url': 'https://arxiv.org/html/2412.14171v2', 'section': 'Appendix B.1',
                'quote': 'The room size is calculated by the Alpha shape algorithm with the scene’s point cloud.'},
            'selection': 'First room-size rows in the frozen common membership order; no answer or score-based replacement',
            'common_room_rows': len(rooms), 'audited_rows': len(output), 'audited_unique_scenes': len({(r['dataset'], r['scene']) for r in output}),
            'common_room_physical_scene_overlap_with_full_vsibench': sum(scene_key(row['dataset'], row['scene']) in benchmark_groups for row in rooms),
            'source_audit': source_audit, 'rows': output,
            'summary': {'reference_rows': len(ratios), 'missing_or_conflicting_reference_rows': len(output) - len(ratios),
                        'same_scene_vsibench_reference_rows': sum(row['vsibench_same_scene_reference'] is not None for row in output),
                        'median_target_to_reference': statistics.median(ratios) if ratios else None,
                        'minimum_target_to_reference': min(ratios) if ratios else None,
                        'maximum_target_to_reference': max(ratios) if ratios else None,
                        'target_below_half_reference': sum(value < 0.5 for value in ratios),
                        'target_below_reference': sum(value < 1 for value in ratios)},
            'diagnostic_only': True, 'training_data_changed': False, 'gpu_jobs': 0, 'gemini_calls': 0,
            'exact_benchmark_alpha_reproduction': False,
            'interpretation': 'Published same-scene training labels are not held-out benchmark labels. Alpha geometry is a sensitivity diagnostic, not invented benchmark ground truth.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--common-done', type=Path, required=True)
    parser.add_argument('--conventions', type=Path, required=True)
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--skip-geometry', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(args.output.resolve().is_relative_to('/data2'), 'room_audit_output_root')
    result = audit(args.common_done, args.conventions, args.limit, not args.skip_geometry)
    write_new(args.output, result)
    print(canonical({'output': str(args.output), 'summary': result['summary']}), flush=True)


if __name__ == '__main__':
    main()
