"""Read completed ScanNet jobs; write v2 checks without changing source artifacts."""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import struct
import numpy as np
from gt_scene_assets import pin, read_json, verify, validate_scene, load_arrays
from scannet_adapter import membership_boxes
from scannet_checks import (source_identity, validate_identity_receipt, require_box_declaration,
                            RECOVERY_FIELDS, validate_recovery_receipt, validate_registry_recovery)
from scannet_sens import SensReader, calibrated_header, rigid, pose_at_slot
from prepare_gt_scene import load_mesh

BASE = Path('/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/materialization_v2')


def utc():
    return datetime.now(timezone.utc).isoformat()


def check_job(job):
    result = dict(scene=job.name, checked_at=utc(), status='would-be-refused', checks={}, reasons=[],
                  registry_entries=[], collector_admission=False)

    def check(name, fn):
        try:
            fn()
            result['checks'][name] = 'passed'
        except Exception as error:
            result['checks'][name] = 'refused'
            result['reasons'].append(dict(check=name, reason=f'{type(error).__name__}: {error}'))

    try:
        terminal = read_json(job / 'TERMINAL.json')
        if terminal['status'] != 'completed' or terminal['scene'] != job.name:
            raise ValueError('not a completed scene terminal')
        result['terminal'] = pin(job / 'TERMINAL.json')
        validation = read_json(verify(terminal['validation']))
        if validation['status'] != 'PASS' or validation['scene'] != job.name:
            raise ValueError('wrapper validation scene/status mismatch')
        result['scene_receipt'] = validation['scene_receipt']
        receipt = read_json(verify(validation['scene_receipt']))
        if receipt['scene_name'] != job.name or receipt['dataset'] != 'scannet':
            raise ValueError('scene receipt identity mismatch')
        result['question_count'] = validation['membership']['question_count']
        source = read_json(verify(receipt['source_provenance']))
        instances = read_json(verify(receipt['instances']))
        evidence = read_json(verify(validation['preparer_validation']))
        frames = read_json(verify(source['source_frames_receipt']))
        raw = source['raw_sources']
        sensor = SensReader(raw['sensor']['path'], header_only=True)
    except Exception as error:
        result['reasons'].append(dict(check='terminal_and_asset_binding', reason=f'{type(error).__name__}: {error}'))
        return result

    def actual_identity():
        binding = source_identity(job.name, frames, source['source_frames_receipt'], raw, sensor)
        result['observed_source_identity'] = binding
        if any(source['source_header'].get(k) != v for k, v in sensor.header.items()):
            raise ValueError('source header differs from actual sensor header')
        if evidence['raw_sources'] != raw or evidence['frames_receipt'] != source['source_frames_receipt']:
            raise ValueError('preparer/source receipt bindings disagree')
    check('R1_actual_source_identity', actual_identity)
    check('R1_bound_identity_receipt', lambda: validate_identity_receipt(receipt, sensor))

    def preparation_binding():
        for name in ('INPUT_RECEIPT.json', 'VALIDATION_RECEIPT.json'):
            value = read_json(job / 'assets' / name)
            if value.get('source_identity') != result.get('observed_source_identity') or 'source_identity' not in value:
                raise ValueError(name + ' lacks the verified source identity binding')
    check('R1_preparation_receipts', preparation_binding)
    for name, value in [('carrier', instances), ('provenance', source), ('scene_receipt', receipt['instances']),
                        ('validation_receipt', evidence), ('input_receipt', read_json(job / 'assets/INPUT_RECEIPT.json'))]:
        check('R2_' + name, lambda value=value, name=name: require_box_declaration(value, name))

    def boxes():
        vertices, faces = load_mesh(verify(raw['mesh'], prepared=False))
        groups, face_ids, vertex_ids, _ = membership_boxes(vertices, faces,
            read_json(verify(raw['segmentation'], prepared=False)),
            read_json(verify(raw['aggregation'], prepared=False)), job.name)
        if instances['segGroups'] != groups:
            raise ValueError('instance boxes/labels differ from all-member min/max convention')
        mesh = load_arrays(receipt['instance_mesh'])
        if not (np.array_equal(mesh['vertices_world'], vertices) and np.array_equal(mesh['faces'], faces)
                and np.array_equal(mesh['face_instance_ids'], face_ids)):
            raise ValueError('instance mesh/source membership mismatch')
        members = load_arrays(source['vertex_membership'])
        if not np.array_equal(members['vertex_instance_ids'], vertex_ids):
            raise ValueError('vertex membership carrier mismatch')
    check('R2_computed_boxes_and_membership', boxes)

    def cameras():
        calibrated_header(sensor.header)
        alignment = read_json(verify(receipt['alignment']))
        calibration = load_arrays(receipt['calibration'])
        if len(alignment['frames']) != 32 or alignment['validated_slots'] != 32:
            raise ValueError('not 32 aligned slots')
        interpolated, offsets = validate_recovery_receipt(receipt, alignment, calibration)
        for field in RECOVERY_FIELDS:
            if any(value.get(field, []) != receipt.get(field, []) for value in (source, evidence)):
                raise ValueError('recovery provenance/validation mismatch: ' + field)
        recovered_sensor = SensReader(sensor.path) if interpolated or offsets else None
        for slot, frame in enumerate(receipt['frames']):
            record = alignment['frames'][slot]
            raw_ordinal = frame['ordinal'] + offsets.get(slot + 1, {}).get('offset', 0)
            if record['ordinal'] != frame['ordinal'] or record['source_frame_id'] != raw_ordinal:
                raise ValueError('selected ordinal/record identity mismatch')
            offset = record['record_offset']
            if type(offset) is not int or offset < sensor.header_pin['size_bytes'] or offset + 64 > sensor.size:
                raise ValueError('selected pose offset outside sensor stream')
            with sensor.path.open('rb') as handle:
                handle.seek(offset)
                raw_pose = np.asarray(struct.unpack('<16f', handle.read(64))).reshape(4, 4)
            if slot + 1 in interpolated or slot + 1 in offsets:
                if recovered_sensor.records[raw_ordinal]['record_offset'] != offset:
                    raise ValueError('recovered source frame/record offset mismatch')
            if slot + 1 in interpolated:
                pose, recovery = pose_at_slot(recovered_sensor.records, raw_ordinal, slot + 1)
                if recovery != interpolated[slot + 1]:
                    raise ValueError('interpolated pose does not use the nearest finite neighbors')
            else:
                pose = rigid(raw_pose, 'selected official pose')
            if not np.array_equal(calibration['camera_poses'][slot], pose.astype(np.float32)):
                raise ValueError('official pose/carrier mismatch')
            if alignment['frames'][slot]['raw_to_vsi_correlation'] < .99:
                raise ValueError('correlation below 0.99')
    check('finite_official_poses_and_recorded_correspondence', cameras)
    # Failed scenes already have a conclusive admission refusal; avoid loading dense rasters twice.
    if not result['reasons']:
        check('v2_collector_admission', lambda: validate_scene(receipt, load_dense=True))
    if not result['reasons']:
        result['status'] = 'passed'
    result['neighbor_separation'] = 'not certified; correlation-only evidence'
    result['registration'] = 'interface/internal consistency only; no independent registration claim'
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--jobs', type=Path, default=BASE / 'jobs_scannet_v1')
    parser.add_argument('--ready', type=Path, default=BASE / 'ready_scannet_v1')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.workers <= 8:
        raise ValueError('workers must be between 1 and 8')
    out = args.out.resolve()
    if out.is_relative_to(args.jobs.resolve()) or out.is_relative_to(args.ready.resolve()):
        raise ValueError('verification output must not modify jobs or registries')
    (out / 'REVERIFY').mkdir(parents=True, exist_ok=True)
    started = utc()
    terminals = {p.parent.name: read_json(p) for p in sorted(args.jobs.glob('*/TERMINAL.json'))}
    completed = [s for s, t in terminals.items() if t.get('status') == 'completed']
    registries = []
    for path in sorted(args.ready.glob('REGISTRY_[0-9]*.json')):
        registries.append((pin(path), read_json(path)))
    rows = []
    heartbeat = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for row in executor.map(check_job, [args.jobs / scene for scene in completed]):
            scene = row['scene']
            for spec, registry in registries:
                # Registry rows are immutable scene-receipt pins. Record their exact JSON location.
                for index, entry in enumerate(registry.get('receipts', [])):
                    if entry.get('path') == row.get('scene_receipt', {}).get('path'):
                        row['registry_entries'].append(dict(registry=spec, json_pointer=f'/receipts/{index}', entry=entry))
                        if any(field in entry for field in RECOVERY_FIELDS):
                            try:
                                validate_registry_recovery(entry, read_json(verify(row['scene_receipt'])))
                                row['checks'].setdefault('recovery_registry_fields', 'passed')
                            except Exception as error:
                                row['status'] = 'would-be-refused'
                                row['checks']['recovery_registry_fields'] = 'refused'
                                row['reasons'].append(dict(check='recovery_registry_fields', reason=f'{type(error).__name__}: {error}'))
            (out / 'REVERIFY' / (scene + '.json')).write_text(json.dumps(row, indent=2, sort_keys=True) + '\n')
            rows.append(row)
            print(json.dumps(dict(scene=scene, status=row['status'], reasons=len(row['reasons']))), flush=True)
            if time.monotonic() - heartbeat >= 300:
                with (out / 'HEARTBEAT.log').open('a') as f: f.write(utc() + ' | reverify ' + scene + '\n')
                heartbeat = time.monotonic()
    summary = dict(started_at=started, finished_at=utc(), jobs=str(args.jobs), ready=str(args.ready),
        completed_at_snapshot=len(completed), terminal_counts=dict(Counter(t['status'] for t in terminals.values())),
        passed=[r['scene'] for r in rows if r['status'] == 'passed'],
        excluded=[r['scene'] for r in rows if r['status'] != 'passed'],
        reason_counts=dict(Counter(reason['check'] for row in rows for reason in row['reasons'])),
        scenes=rows, paid_api_calls=0, gpu_runs=0, collector_admission=False)
    summary['passed_count'] = len(summary['passed'])
    summary['excluded_count'] = len(summary['excluded'])
    (out / 'REVERIFY_SUMMARY.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('scenes','passed','excluded')}), flush=True)


if __name__ == '__main__':
    main()
