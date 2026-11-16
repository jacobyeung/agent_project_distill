import hashlib
import json
from collections import Counter
from pathlib import Path


TYPES = ('camera_displacement', 'camera_movement_direction', 'camera_rotation')
FROZEN_COHORT_SHA = '639a6614a9c5bfe5ebb2d795ba3892766110cc09943aa3d155745a345ee322fd'


def local(path):
    p = Path(path).resolve()
    if p.parts[1:2] == ('home',) or (len(p.parts) > 1 and p.parts[1].startswith('data')):
        raise ValueError('Forbidden shared-filesystem path: ' + str(p))
    return p


def sha(path):
    with local(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def pin(path):
    return dict(path=str(local(path)), sha256=sha(path))


def load(path):
    return json.loads(local(path).read_text())


def checked(value):
    if sha(value['path']) != value['sha256']:
        raise ValueError('Camera cohort pin mismatch: ' + value['path'])
    return local(value['path'])


def load_tasks(receipt_pin, frames_pin):
    if receipt_pin.get('sha256') != FROZEN_COHORT_SHA:
        raise ValueError('Camera cohort differs from the pre-read freeze')
    receipt = load(checked(receipt_pin))
    if receipt.get('schema') != 'legs1-camera-cohort-v1' or receipt.get('frozen') is not True:
        raise ValueError('Camera cohort is not frozen')
    if receipt['frames']['sha256'] != frames_pin['sha256']:
        raise ValueError('Camera cohort RGB32 manifest differs')
    checked(frames_pin)
    if receipt.get('model_reads_before_freeze') != 0:
        raise ValueError('Camera cohort selection must precede model reads')
    tasks = [json.loads(line) for line in checked(receipt['tasks']).read_text().splitlines() if line]
    if len(tasks) != 450 or len({t['id'] for t in tasks}) != 450:
        raise ValueError('Camera cohort membership differs')
    counts = Counter(t['question_type'] for t in tasks)
    if dict(counts) != {t: 150 for t in TYPES} or dict(counts) != receipt['counts']:
        raise ValueError('Camera cohort type counts differ')
    if digest([t['id'] for t in tasks]) != receipt['ordered_ids_sha256']:
        raise ValueError('Camera cohort order differs')
    captures = {c['native']: c for c in load(checked(frames_pin))['captures']}
    for task in tasks:
        capture = captures[task['native']]
        if (task['source_frame_indices'] != capture['anchor_indices']
                or task['rgb32_sha256'] != digest(capture['frames'])
                or task.get('stratum') != 'camera_gt'
                or task.get('label_authority') != 'native_camera_gt'):
            raise ValueError('Camera task GT/frame contract differs')
        pair = task.get('display_frame_pair')
        if (not isinstance(pair, list) or len(pair) != 2
                or any(type(v) is not int for v in pair) or not 1 <= pair[0] < pair[1] <= 32):
            raise ValueError('Camera task frame pair differs')
    return tasks
