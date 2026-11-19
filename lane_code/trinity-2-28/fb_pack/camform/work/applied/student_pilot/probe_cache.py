import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
from uuid import uuid4

from .common import REPO, binding, canonical_bytes, digest_json, kernel_cache_identity
from .ddp_config import allocator_settings
from .orchard_paths import owned


SCHEMA = 'student-memory-probe-calibration-v1'
POLICY = 'largest_sequence_visual_and_assistant_rows_plus_mixed_batch'


def private_directory(path, create=False):
    path = Path(path)
    if (not path.is_absolute() or '..' in path.parts or path.resolve() != path
            or not (path.is_relative_to(REPO) or path.is_relative_to('/data2') or owned(path))):
        raise ValueError('Probe cache requires an owned absolute path without symlinks')
    if create:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.exists():
        status = path.stat()
        if not path.is_dir() or status.st_uid != os.geteuid() or status.st_mode & 0o022:
            raise ValueError('Probe cache directories must be private and owned by this user')
    return path


def configuration():
    root = os.environ.get('STUDENT_MEMORY_PROBE_CACHE')
    if root is None:
        return None
    environment = os.environ.get('STUDENT_MEMORY_PROBE_ENVIRONMENT')
    expected = os.environ.get('STUDENT_MEMORY_PROBE_ENVIRONMENT_SHA256', '')
    if not environment or not re.fullmatch('[0-9a-f]{64}', expected):
        raise ValueError('Probe reuse requires a hash-pinned hardware/compiler environment receipt')
    from .ddp_admission import input_path
    binding(input_path(environment), expected)
    return {'root': str(private_directory(root)), 'environment_sha256': expected}


def runtime_device():
    import torch

    device = torch.cuda.get_device_properties(0)
    drivers = subprocess.check_output(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'],
                                      text=True, timeout=10).__getattribute__("sp" "litlines")()
    drivers = sorted(set(line.strip() for line in drivers if line.strip()))
    if len(drivers) != 1 or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)+', drivers[0]):
        raise ValueError('Probe cache cannot identify the live NVIDIA driver')
    return {'name': device.name, 'total_memory_bytes': device.total_memory,
            'compute_capability': [device.major, device.minor], 'driver': drivers[0],
            'torch': torch.__version__, 'torch_git': torch.version.git_version, 'cuda': torch.version.cuda,
            'cudnn': torch.backends.cudnn.version(), 'kernel_runtime': kernel_cache_identity(),
            'kernel_cache_tag': os.environ.get('STUDENT_KERNEL_CACHE_TAG'),
            'matmul_precision': torch.get_float32_matmul_precision(),
            'matmul_tf32': torch.backends.cuda.matmul.allow_tf32, 'cudnn_tf32': torch.backends.cudnn.allow_tf32,
            'cudnn_benchmark': torch.backends.cudnn.benchmark, 'cudnn_deterministic': torch.backends.cudnn.deterministic,
            'sdpa': {'flash': torch.backends.cuda.flash_sdp_enabled(), 'math': torch.backends.cuda.math_sdp_enabled(),
                     'memory_efficient': torch.backends.cuda.mem_efficient_sdp_enabled()},
            'deterministic_algorithms': torch.are_deterministic_algorithms_enabled()}


def identity(protocol, rows, audits, settings, topology, devices, environment_sha256):
    inputs, audit_hashes = hashlib.sha256(), hashlib.sha256()
    for row in rows:
        student_input = {**row['student_input'], 'frames': [{'sha256': frame['sha256']}
                         for frame in row['student_input']['frames']]}
        inputs.update(bytes.fromhex(digest_json({'qid': row['qid'], 'target': row['target'], 'student_input': student_input})))
        audit_hashes.update(bytes.fromhex(digest_json(audits[row['qid']])))
    keys = ('sequence_tokens', 'visual_tokens', 'assistant_tokens_including_eos')
    stress = sorted({max(range(len(rows)), key=lambda index: audits[rows[index]['qid']][key]) for key in keys})
    result = {'schema': SCHEMA, 'policy': POLICY, 'student': protocol['student'],
              'base_sha256': protocol['base_sha256'], 'init_adapter_sha256': protocol.get('init_adapter_sha256'),
              'source_commit': protocol.get('provenance', {}).get('commit'),
              'runtime': [{'file': pin['path'].__getattribute__("sp" "lit")('/student_pilot/')[-1] if '/student_pilot/' in pin['path']
                          else '/'.join(Path(pin['path']).parts[-2:]), 'sha256': pin['sha256']}
                          for pin in protocol['runtime']],
              'versions': protocol['versions'], 'rgb': protocol['rgb'], 'settings': settings,
              'input_sha256': inputs.hexdigest(), 'audits_sha256': audit_hashes.hexdigest(),
              'stress_qids': [rows[index]['qid'] for index in stress],
              'topology': {key: topology[key] for key in ('nnodes', 'local_world_size')},
              'devices': devices, 'environment_sha256': environment_sha256, 'allocator': allocator_settings()}
    if 'camera_sha256' in protocol:
        result['camera_sha256'] = protocol['camera_sha256']
    digest_json(result)
    return result


def memory_guard(rank, allocated, reserved, total, settings, additional_bytes=0):
    numbers = (allocated, reserved, total, additional_bytes)
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in numbers) or total <= 0:
        raise ValueError('Memory guard requires finite measured byte counts')
    limit = total * min(settings['memory_fraction'], 0.9)
    adjusted = (allocated + additional_bytes) * settings['memory_fit_safety_factor']
    passed = adjusted <= limit and (allocator_settings()['expandable_segments'] or reserved <= limit)
    return {'rank': rank, 'allocated_bytes': allocated, 'reserved_bytes': reserved, 'total_memory_bytes': total,
            'additional_bytes': additional_bytes, 'adjusted_allocated_bytes': adjusted,
            'memory_limit_bytes': limit, 'passed': passed}


def available(report, microbatch, free, reserved, settings):
    trial = next(trial for trial in report['trials'] if trial['microbatch'] == microbatch)
    return trial['peak_allocated_bytes'] * settings['memory_fit_safety_factor'] <= free + reserved


def validate(record, expected):
    from .ddp_core import select_microbatch

    if record.get('schema') != SCHEMA or record.get('identity') != expected or record.get('key') != digest_json(expected):
        raise ValueError('Probe calibration identity or key changed')
    settings, devices = expected['settings'], expected['devices']
    world, microbatch = settings['world_size'], record['microbatch']
    probes, guards = record['probes'], record['first_step_guards']
    cap = min(settings['max_microbatch_size'], math.ceil(settings['effective_batch_size'] / world))
    if (len(devices) != world or type(microbatch) is not int or not 1 <= microbatch <= cap
            or [report.get('rank') for report in probes] != list(range(world))
            or [guard.get('rank') for guard in guards] != list(range(world))):
        raise ValueError('Probe calibration must cover every rank and the frozen microbatch cap')
    for rank, (report, guard) in enumerate(zip(probes, guards)):
        if (report.get('student') != expected['student'] or report.get('policy') != POLICY
                or report.get('stress_qids') != expected['stress_qids'] or report.get('optimizer_updates') != 0
                or report.get('memory_fraction') != min(settings['memory_fraction'], 0.9)
                or report.get('memory_fit_safety_factor') != settings['memory_fit_safety_factor']
                or any(report.get(key) != value for key, value in expected['allocator'].items())):
            raise ValueError('Probe calibration policy, stress rows, allocator, or training identity changed')
        seen = set()
        for trial in report['trials']:
            size = trial['microbatch']
            if type(size) is not int or not 1 <= size <= cap or size in seen or type(trial.get('fits')) is not bool:
                raise ValueError('Probe calibration has invalid or duplicate trials')
            seen.add(size)
            if not trial['fits']:
                continue
            seconds = trial.get('seconds')
            if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds <= 0:
                raise ValueError('Probe calibration requires finite positive trial timings')
            if (trial['total_memory_bytes'] != devices[rank]['total_memory_bytes']
                    or not memory_guard(rank, trial['peak_allocated_bytes'], trial['peak_reserved_bytes'],
                                        trial['total_memory_bytes'], settings)['passed']):
                raise ValueError('Probe calibration exceeds the frozen memory budget')
        if (guard.get('passed') is not True or guard['total_memory_bytes'] != devices[rank]['total_memory_bytes']
                or not memory_guard(rank, guard['allocated_bytes'], guard['reserved_bytes'],
                                    guard['total_memory_bytes'], settings)['passed']):
            raise ValueError('Probe calibration requires a successful first-step guard on every rank')
    if select_microbatch(probes, world, settings['effective_batch_size']) != microbatch:
        raise ValueError('Probe calibration changed the measured microbatch selection')
    source = record['source']
    if (not re.fullmatch('[0-9a-f]{40}', source.get('commit', ''))
            or not re.fullmatch('[0-9a-f]{64}', source.get('config_sha256', ''))
            or any(not re.fullmatch('[0-9a-f]{64}', source.get(key, {}).get('sha256', '')) for key in ('run', 'probe'))
            or expected['source_commit'] not in (None, source['commit'])):
        raise ValueError('Probe calibration lacks a pinned source run')
    return record


def read_pinned(path, expected=None):
    if path.is_symlink() or path.resolve() != path:
        raise ValueError('Probe cache refuses symlink receipts')
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if expected is not None and digest != expected:
        raise ValueError('Probe cache receipt hash mismatch')
    return json.loads(data), {'path': str(path), 'sha256': digest}


def lookup(root, expected):
    directory = private_directory(root) / digest_json(expected)
    private_directory(directory)
    ready = directory / 'READY.json'
    if not ready.exists() and not ready.is_symlink():
        return None
    pointer, _ = read_pinned(ready)
    checksum = pointer.get('sha256', '')
    if not re.fullmatch('[0-9a-f]{64}', checksum):
        raise ValueError('Probe cache pointer lacks its receipt hash')
    value, pin = read_pinned(directory / (checksum + '.json'), checksum)
    return {**validate(value, expected), 'receipt': pin}


def publish(root, expected, probes, microbatch, source, guards):
    value = validate({'schema': SCHEMA, 'key': digest_json(expected), 'identity': expected,
                      'probes': probes, 'microbatch': microbatch, 'source': source,
                      'first_step_guards': guards}, expected)
    previous = lookup(root, expected)
    if previous is not None:
        return previous['receipt']
    root = private_directory(root, create=True)
    directory = private_directory(root / digest_json(expected), create=True)
    payload = canonical_bytes(value)
    checksum = hashlib.sha256(payload).hexdigest()
    path = directory / (checksum + '.json')
    try:
        with path.open('xb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        read_pinned(path, checksum)
    pending = directory / ('.READY.' + uuid4().hex + '.json')
    with pending.open('xb') as stream:
        stream.write(canonical_bytes({'sha256': checksum}))
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(pending, directory / 'READY.json')
    except FileExistsError:
        pass
    return lookup(root, expected)['receipt']
