"""Population and compact-result adapter for family r6."""
from collections import Counter
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c6

CONSTANTS = {'camera_obj_rel_dist_v1':25.3, 'camera_obj_rel_dist_v2':33.3,
             'camera_obj_rel_dist_v3':50.0, 'obj_obj_relative_pos_lr':50.0,
             'obj_obj_relative_pos_nf':50.0, 'obj_obj_relative_pos_ud':50.0}
COUNTS = {name:150 for name in CONSTANTS}
CAPTURE_SHA256 = 'bbc735c3daf0fe8a7126883cb955097a1e52a2dcc738a19b902cb8e8c120c87b'


def check_capture(registration):
    if (registration['capture_sha256'] != CAPTURE_SHA256
            or hashlib.sha256(Path(c6.__file__).read_bytes()).hexdigest() != CAPTURE_SHA256):
        raise ValueError('Capture pin differs')


def validate_items(rows, registration):
    if len(rows) != 900 or len({r['id'] for r in rows}) != 900:
        raise ValueError('Item membership differs')
    if Counter(r['question_type'] for r in rows) != COUNTS or registration['type_counts'] != COUNTS:
        raise ValueError('Type denominator differs')
    if len({r['room'] for r in rows}) != 68:
        raise ValueError('Room membership differs')
    refs = set()
    for row in rows:
        indices = row['source_frame_indices']
        if (len(indices) != 32 or indices != sorted(set(indices)) or len(row['frame_refs']) != 32
                or any(type(i) is not int or not 0 <= i < row['total_num_frames'] for i in indices)):
            raise ValueError('Invalid frame selection')
        options = row['options']
        expected_options = 4 if row['question_type'].endswith('_v1') else 3 if row['question_type'].endswith('_v2') else 2
        if (row['id'] != row['example_id'] or row['scene'] != row['room'] or row['fps'] <= 0
                or row['answer_type'] != 'multiple_choice' or row['thinking'] is not True
                or len(options) != expected_options or row['answer'] != row['ground_truth']
                or row['answer'] not in list('ABCD'[:len(options)])
                or any(not option.startswith(chr(65+i)+'. ') for i,option in enumerate(options))):
            raise ValueError('Invalid MC metadata')
        refs.update(row['frame_refs'])
    if refs != set(registration['used_frames']) or not refs <= set(registration['frames']):
        raise ValueError('Frame inventory differs')
    return rows


def compact(scored, tasks, step):
    from evalpath.official import official_fuzzy_matching
    by_id = {r['id']:r for r in tasks}
    if len(scored) != len(by_id) or {r['id'] for r in scored} != set(by_id):
        raise ValueError('Return membership differs')
    result = []
    for row in scored:
        task = by_id[row['id']]
        if (row['status'] != 'complete' or row['score'] not in (0,1)
                or row['question_type'] != task['question_type'] or row['room'] != task['room']):
            raise ValueError('Incomplete or mismatched output')
        letter = official_fuzzy_matching(row['extracted_answer']).upper()
        letter = letter if letter in list('ABCD'[:len(task['options'])]) else None
        # Continuation raw_generation contains only the answer; scoring_text also
        # retains the authenticated generated thinking prefix. Reused ON rows use raw_generation.
        trace = row['scoring_text'] if 'scoring_text' in row else row['raw_generation']
        if not isinstance(trace, str):raise ValueError('Missing model trace')
        result.append(dict(id=row['id'], family='r6', room=row['room'], scene=row['scene'],
            task_type=row['question_type'], prediction=letter, predicted_letter=letter,
            gold_letter=task['answer'], score=int(row['score']), budget=2048, step=step,
            scoring_basis='answer', template_capture=c6.flag(trace),
            trace_sha256=hashlib.sha256(trace.encode()).hexdigest()))
    return result
