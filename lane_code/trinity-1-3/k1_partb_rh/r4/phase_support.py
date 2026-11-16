"""Reviewable phase checks; these functions do not authorize a GPU launch."""
import json
import math
from pathlib import Path
import re
import shutil


def require_manifest_pins(manifest):
    for key in ('artifact', 'config', 'data_receipt'):
        pin = manifest['gpu'][key]
        if not re.fullmatch('[0-9a-f]{64}', pin.get('sha256', '')):
            raise ValueError('Unbound ' + key + ' SHA256: ' + repr(pin.get('sha256')))
        if 'REQUIRED' in pin.get('path', ''):
            raise ValueError('Unbound ' + key + ' path: ' + pin['path'])


def compare_binding(B, phases, manifest, reference):
    expected = dict(manifest_sha256=B.digest(manifest), sources=B.source_identity(),
                    producer_sha256=B.sha(phases.__file__))
    for key, value in expected.items():
        if reference.get(key) != value:
            raise ValueError('Reference binding differs: ' + key)
    return expected


def space_report(paths):
    result = {}
    for name, path in paths.items():
        p = Path(path)
        while not p.exists():
            p = p.parent
        usage = shutil.disk_usage(p)
        result[name] = dict(path=str(path), measured_at=str(p), free=usage.free,
                            total=usage.total)
    return result


def budget(elapsed, longest_capture, margin, allocation=43200, *,
           deadline_unix=None, started_unix=None):
    if deadline_unix is not None:
        if started_unix is None or not all(math.isfinite(x) for x in (deadline_unix, started_unix)):
            raise ValueError('Deadline requires finite absolute start and deadline times')
        allocation = min(allocation, deadline_unix - started_unix)
    values = (elapsed, longest_capture, margin)
    if not all(math.isfinite(x) and x >= 0 for x in values) or longest_capture <= 0:
        raise ValueError('Budget requires measured finite timings and a positive capture bound')
    if not math.isfinite(allocation):
        raise ValueError('Allocation must be finite')
    seconds = max(0, math.floor(allocation - elapsed - longest_capture - margin))
    return dict(allocation_seconds=allocation, setup_and_elapsed_seconds=elapsed,
                longest_capture_seconds=longest_capture, margin_seconds=margin,
                max_seconds=seconds)


def refuse_incomplete(B, manifest, root):
    root = Path(root)
    if (root / 'HALTED.json').exists():
        raise ValueError('HALTED root requires operator review')
    for capture in manifest['captures']:
        dest = root / B.digest(capture['canonical'])[:16]
        if dest.exists() and not (dest / 'PHASE_COMPLETE.json').is_file():
            raise ValueError('Incomplete capture preserved; operator review and fresh root required')


def canary(B, phases, manifest, root, expected_synthetic, timing_limit):
    import numpy as np
    root = Path(root)
    try:
        rows = [json.loads(s) for s in (root / 'PROGRESS.jsonl').read_text().splitlines()]
        timings = []
        for capture in manifest['captures'][:3]:
            dest, receipt = phases.checked_phase(capture, root, 'own')
            if receipt['synthetic'] is not expected_synthetic:
                raise ValueError('Canary synthetic identity differs')
            with np.load(dest / 'own.npz', allow_pickle=False) as arrays:
                depth, gravity = arrays['depth'], arrays['gravity']
                if depth.shape != (32, 51, 51) or not np.isfinite(depth).all() or (depth <= 0).any():
                    raise ValueError('Canary depth differs')
                if gravity.shape not in ((3,), (32, 3)) or not np.isfinite(gravity).all():
                    raise ValueError('Canary gravity differs')
            start = next(r['unix'] for r in rows if r['event'] == 'capture_start'
                         and r['canonical'] == capture['canonical'])
            commit = next(r['unix'] for r in rows if r['event'] == 'capture_commit'
                          and r['canonical'] == capture['canonical'])
            seconds = commit - start
            if not math.isfinite(seconds) or not 0 < seconds <= timing_limit:
                raise ValueError('Canary timing differs')
            timings.append(seconds)
        return dict(passed=True, captures=3, seconds=timings, longest_seconds=max(timings))
    except Exception as error:
        with (root / 'STOP').open('x') as stream:
            stream.write('Canary failed: ' + str(error) + '\n')
        return dict(passed=False, error=str(error))
