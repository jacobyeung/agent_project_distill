import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re

from .common import binding, canonical_bytes, digest_json, io_threads, ordered_io, resolve_read
from .provisional import require_mode, source_path, tag, target_span


SCHEMA = 'student-cpu-startup-validation-v1'
FROZEN_FILES = ('config.json', 'launch_identity.json', 'protocol.json', 'training.json',
                'training.json.source_receipt.json', 'request.json')


def frame_references(rows):
    frames = {}
    for row in rows:
        for frame in row['student_input']['frames']:
            previous = frames.setdefault(frame['path'], frame)
            if previous != frame or not re.fullmatch('[0-9a-f]{64}', frame['sha256']):
                raise ValueError('Shared frame references disagree about their admitted bytes')
    return [frames[path] for path in sorted(frames)]


def dropped_dependencies(protocol, manifest, label):
    from . import provisional_data as data
    from .provisional import candidate_entries

    dropped = {item['qid'] for item in manifest['pre_evaluation_drops']}
    if not dropped:
        return []
    entries, source = candidate_entries(protocol['candidate_source']['path'], label)
    pins = [binding(source)]
    for entry in entries:
        if entry['qid'] not in dropped:
            continue
        for name, checksum in (('target_path', 'sha256'), ('row_path', 'row_sha256')):
            if name in entry:
                if name == 'target_path' and target_span(entry) is not None:
                    # A sharded target's sha256 pins its byte range, which the loader checks; pin the whole shard here.
                    pins.append(binding(source_path(entry[name], source.parent)))
                else:
                    pins.append(binding(source_path(entry[name], source.parent), entry[checksum]))
    rows = data._census_rows(protocol, dropped, label)
    pins += frame_references(list(rows.values()))
    return list({(pin['path'], pin['sha256']): pin for pin in pins}.values())


def require_cpu():
    if (os.environ.get('CUDA_VISIBLE_DEVICES') != ''
            or any(os.environ.get(key, '') not in ('', 'N/A', '(null)') for key in ('SLURM_JOB_GPUS', 'SLURM_STEP_GPUS'))
            or os.environ.get('SLURM_GPUS_ON_NODE', '') not in ('', '0', 'N/A', '(null)')):
        raise ValueError('Shared startup validation requires a CPU allocation with CUDA hidden')


def read_document(path, expected=None):
    from .ddp_admission import input_path

    path = input_path(path)
    payload = resolve_read(path).read_bytes()
    pin = {'path': str(path), 'sha256': hashlib.sha256(payload).hexdigest()}
    if expected is not None and pin != expected:
        raise ValueError('Startup input hash or path changed: ' + str(path))
    return json.loads(payload), pin


def prepare(frozen, student, world_size, label):
    from . import ddp_admission, orchard_paths, provisional_data as data, storage

    require_cpu()
    frozen = ddp_admission.input_path(frozen)
    output, inventory_path = frozen / 'startup_receipt.json', frozen / 'shared_frames.json'
    if any(path.exists() or path.is_symlink() for path in (output, inventory_path)):
        raise ValueError('Startup preparation requires new immutable output paths')
    if not orchard_paths.enabled():
        raise ValueError('Shared frame startup requires the explicit Orchard site')
    pins = {name: binding(frozen / name) for name in FROZEN_FILES}
    protocol = data.load_protocol(frozen / 'protocol.json', label, student=student)
    manifest = data.load_training(frozen / 'training.json', label)
    request = ddp_admission.checked_request(frozen / 'request.json', label)
    if (protocol['student'] != student or request['student'] != student or request['world_size'] != world_size
            or protocol['training']['world_size'] != world_size
            or request['manifest'] != pins['training.json'] or request['protocol'] != pins['protocol.json']
            or manifest['protocol'] != pins['protocol.json'] or not manifest['training_ready'] or not manifest['rows']):
        raise ValueError('CPU startup identity differs from its admitted protocol and training request')
    references = frame_references(manifest['rows'])

    def verify_frame(pin):
        path = resolve_read(source_path(pin['path'])).resolve()
        if not path.is_relative_to(orchard_paths.PROJECT) or path == orchard_paths.PROJECT:
            raise ValueError('CPU-prepared frames must remain on shared Orchard storage, not node-local scratch')
        binding(pin['path'], pin['sha256'])
        return {**pin, 'size_bytes': path.stat().st_size}

    with ThreadPoolExecutor(max_workers=io_threads()) as pool:
        files = list(ordered_io(pool, verify_frame, references, io_threads() * 2))
    dependencies = dropped_dependencies(protocol, manifest, label)
    for pin in dependencies:
        binding(pin['path'], pin['sha256'])
    for name, pin in pins.items():
        if binding(frozen / name) != pin:
            raise ValueError('Frozen startup input changed during CPU validation: ' + name)
    if (read_document(frozen / 'protocol.json', pins['protocol.json'])[0] != protocol
            or read_document(frozen / 'training.json', pins['training.json'])[0] != manifest):
        raise ValueError('CPU validators did not validate the pinned input bytes')
    inventory = {'schema': 'student-shared-frame-inventory-v1', 'manifest': pins['training.json'],
                 'files': files, 'references_sha256': digest_json(references),
                 'unique_paths': len(files), 'total_bytes': sum(item['size_bytes'] for item in files),
                 'frame_mode': 'shared_verified_on_read', 'path_map': os.environ.get(('Q_E4' if 'Q_E4' in os.environ else 'STUDENT_FRAME_ROOT_MAP'))}
    value = tag({'schema': SCHEMA, 'status': 'CPU_VALIDATED_NO_GPU_ADMISSION', 'student': student,
                 'world_size': world_size, 'inputs': pins, 'dropped_dependencies': dependencies,
                 'frame_mode': inventory['frame_mode'], 'path_map': inventory['path_map'],
                 'inventory': {'path': str(inventory_path), 'sha256': hashlib.sha256(canonical_bytes(inventory)).hexdigest()}}, label)
    provenance = storage.code_provenance(value)
    with inventory_path.open('xb') as stream:
        stream.write(canonical_bytes(inventory))
    with output.open('xb') as stream:
        stream.write(canonical_bytes({**value, 'provenance': provenance}))
    return binding(output)


def load_prepared(manifest_path, protocol_path, label, student, weights=False):
    from . import ddp_admission, provisional_data as data, storage

    path = os.environ.get('STUDENT_STARTUP_RECEIPT')
    expected = os.environ.get('STUDENT_STARTUP_RECEIPT_SHA256')
    if path is None and expected is None:
        return None
    if not path or not re.fullmatch('[0-9a-f]{64}', expected or ''):
        raise ValueError('Startup reuse requires both its receipt and external SHA256 pin')
    manifest_path, protocol_path = ddp_admission.input_path(manifest_path), ddp_admission.input_path(protocol_path)
    frozen = manifest_path.parent
    if (manifest_path.name != 'training.json' or protocol_path != frozen / 'protocol.json'
            or Path(path) != frozen / 'startup_receipt.json'):
        raise ValueError('Startup receipt must match the exact frozen input directory')
    receipt, receipt_pin = read_document(path, {'path': str(path), 'sha256': expected})
    require_mode(receipt, label)
    if (receipt.get('schema') != SCHEMA or receipt.get('status') != 'CPU_VALIDATED_NO_GPU_ADMISSION'
            or receipt.get('student') != student or receipt.get('frame_mode') != 'shared_verified_on_read'
            or receipt.get('path_map') != os.environ.get(('Q_E4' if 'Q_E4' in os.environ else 'STUDENT_FRAME_ROOT_MAP'))
            or set(receipt.get('inputs', {})) != set(FROZEN_FILES)):
        raise ValueError('Startup receipt changed its validated identity or shared frame mapping')
    value = {key: item for key, item in receipt.items() if key != 'provenance'}
    provenance = receipt.get('provenance', {})
    if (provenance.get('dirty') is not False or provenance.get('config_sha256') != digest_json(value)
            or provenance.get('commit') != storage.code_provenance(value)['commit']):
        raise ValueError('Startup receipt requires the same clean code commit')
    for name, pin in receipt['inputs'].items():
        if pin != binding(frozen / name):
            raise ValueError('Startup input hash or path changed: ' + name)
    inventory, _ = read_document(frozen / 'shared_frames.json', receipt['inventory'])
    manifest, manifest_pin = data._read_manifest(manifest_path)
    if manifest_pin != receipt['inputs']['training.json']:
        raise ValueError('Training manifest changed while reading the startup receipt')
    protocol = data.load_protocol(protocol_path, label, weights=weights, student=student)
    if (binding(protocol_path) != receipt['inputs']['protocol.json']
            or protocol['training']['world_size'] != receipt['world_size']
            or inventory.get('schema') != 'student-shared-frame-inventory-v1'
            or inventory.get('manifest') != manifest_pin
            or inventory.get('references_sha256') != digest_json(frame_references(manifest['rows']))):
        raise ValueError('Startup protocol or shared frame inventory changed')
    data._verified_receipt(manifest_path, manifest_pin, manifest, protocol, label)
    for pin in receipt['dropped_dependencies']:
        binding(pin['path'], pin['sha256'])
    return {'protocol': protocol, 'manifest': manifest, 'receipt': receipt_pin,
            'inventory': receipt['inventory'], 'frame_mode': receipt['frame_mode']}


def localize_shared(prepared, store, manifest_path):
    rows = prepared['manifest']['rows']
    store.write('shared_frame_admission.json', {'receipt': prepared['receipt'], 'inventory': prepared['inventory'],
                                               'frame_mode': prepared['frame_mode'], 'hash_before_each_decode': True})
    store.write('input_manifest.json', {'source_manifest': binding(manifest_path), 'rows': rows})
    return rows
