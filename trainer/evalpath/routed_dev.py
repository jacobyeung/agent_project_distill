"""Fixed ScanNet validation development population; no test-metadata selection."""
from collections import Counter, defaultdict
import random
import re

from .items import read_rows
from .official import build_prompt_context

TYPES = ('object_rel_direction_medium', 'object_rel_direction_hard', 'object_abs_distance')
POOL_SHA = '9f923ba410a5765231131a241675c585cf7841a207fee4a05f3e29d0855483df'
ROWS_SHA = '8b4caf107e5144eb371db31e28e939e60f4fb12348cdc070a5712a3ea794d3c4'
SEED = 17


def select_rows(population):
    """Shuffle sorted scenes, then take one question per scene before a second."""
    if len({str(r['id']) for r in population}) != len(population):
        raise ValueError('Duplicate development-pool ID')
    rng = random.Random(SEED)
    selected = []
    for kind in TYPES:
        scenes = defaultdict(list)
        for row in population:
            if row['question_type'] == kind:
                if row['dataset'] != 'scannet' or not re.fullmatch(r'scene\d{4}_\d{2}', row['scene_name']):
                    raise ValueError('Development rows require ScanNet validation scenes')
                scenes[row['scene_name']].append(row)
        order = sorted(scenes)
        rng.shuffle(order)
        for scene in order:
            scenes[scene].sort(key=lambda r: str(r['id']))
            rng.shuffle(scenes[scene])
        chosen = []
        for offset in range(2):
            for scene in order:
                if offset < len(scenes[scene]) and len(chosen) < 50:
                    chosen.append(scenes[scene][offset])
        if len(chosen) != 50:
            raise ValueError('Development pool cannot supply 50 per type with scene cap 2')
        selected.extend(chosen)
    return sorted(selected, key=lambda r: str(r['id']))


def selection(rows):
    return dict(pool_sha256=POOL_SHA, seed=SEED, per_type=50, max_per_scene_type=2,
                chosen_ids=[str(r['id']) for r in rows])


def validate_request(request):
    if (request['kind'] != 'routed' or len(request['datasets']) != 1
            or request.get('parity_official') or request.get('routing_heldout')
            or request.get('routed_protocol') != 'routed-types-v1'
            or request.get('max_new_tokens') != 16384 or request.get('enable_thinking') is not True
            or request.get('do_sample') is not False):
        raise ValueError('Development routed protocol differs')
    spec = request['datasets'][0]
    selected = spec.get('selection', {})
    ids = selected.get('chosen_ids', [])
    if (spec['benchmark'] != 'routed_dev' or spec['rows']['sha256'] != ROWS_SHA
            or selected != dict(pool_sha256=POOL_SHA, seed=SEED, per_type=50,
                                max_per_scene_type=2, chosen_ids=ids)
            or len(ids) != 150 or len(set(ids)) != 150 or ids != sorted(ids)):
        raise ValueError('Development membership differs')


def load_tasks(spec, roots):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('evalpath/routed_dev.py:load_tasks')
    if spec['rows']['sha256'] != ROWS_SHA:
        raise ValueError('Development metadata pin differs')
    rows = read_rows(spec['rows'])
    if (len(rows) != 150 or len({str(r['id']) for r in rows}) != 150
            or Counter(r['question_type'] for r in rows) != Counter(dict.fromkeys(TYPES, 50))
            or any(r['dataset'] != 'scannet' for r in rows)
            or max(Counter((r['question_type'], r['scene_name']) for r in rows).values()) > 2
            or spec.get('selection') != selection(rows)):
        raise ValueError('Development rows or recorded IDs differ')
    tasks = []
    for row in rows:
        if not re.fullmatch(r'scene\d{4}_\d{2}', row['scene_name']):
            raise ValueError('Invalid development scene')
        task = {**row, 'example_id': str(row['id']), 'benchmark': 'routed_dev',
                'options': row.get('options') or [],
                'video_path': roots['video_root'].rstrip('/')+'/scannet/'+row['scene_name']+'.mp4'}
        build_prompt_context(task, 'ours')
        tasks.append(task)
    return tasks


def parity_tasks(tasks):
    """One unchanged dev question and one explicit own-camera routing probe."""
    first = min((t for t in tasks if t['question_type'] == TYPES[0]), key=lambda t: t['example_id'])
    source = min((t for t in tasks if t['question_type'] == TYPES[2]), key=lambda t: t['example_id'])
    probe = {**source, 'example_id': source['example_id']+':camera',
             'question_type': 'camera_pose_probe', 'options': [], 'ground_truth': '',
             'question': 'Read the camera pose at Frame 1 using <pose frame=1>. Report the camera values.'}
    return [first, probe]
