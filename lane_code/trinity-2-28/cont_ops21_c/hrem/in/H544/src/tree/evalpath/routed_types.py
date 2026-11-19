"""Pre-registered official VSI routed read and fixed production parity prompts."""
import re

from .items import digest

TYPES = ('object_rel_direction_medium', 'object_rel_direction_hard',
         'object_abs_distance', 'object_rel_direction_easy')
SOURCES = ('scannet', 'scannetpp', 'arkitscenes')


def select(tasks):
    if len(tasks) != 5130:
        raise ValueError('Routed read requires the full official 5130 population')
    rows = [t for t in tasks if t['question_type'] in TYPES]
    if set(t['question_type'] for t in rows) != set(TYPES):
        raise ValueError('Missing pre-registered question type')
    if any(t['dataset'] not in SOURCES for t in rows):
        raise ValueError('Unknown official source')
    return sorted(rows, key=lambda t: t['example_id'])


def parity_tasks(tasks):
    """Five unchanged VSI questions plus one camera probe on the first VSI video."""
    rows = []
    for kind in (*TYPES, 'object_counting'):
        rows.append(min((t for t in tasks if t['question_type'] == kind), key=lambda t: t['example_id']))
    camera = {**rows[0], 'example_id': rows[0]['example_id']+':camera',
              'question_type': 'camera_pose_probe', 'options': [], 'ground_truth': '',
              'question': 'Read the camera pose at Frame 1 using <pose frame=1>. Report the camera values.'}
    return [*rows, camera]


def route_fields(decoded):
    calls, heads, frames = decoded.get('calls', []), [], set()
    enriched = []
    for call in calls:
        text = call['call']
        opener = re.match(r'<(depth_at|move|pose|turn)\b', text)
        is_head = bool(opener) and not (' at=' in text and opener[1] == 'turn')
        used = sorted({int(n) for n in re.findall(r'(?:frame|from|to)=(\d+)\b', text)}) if is_head else []
        if is_head:
            heads.append('<'+opener[1])
            frames.update(used)
        enriched.append({**call, 'frames_used': used, 'frame_count': len(used) if used else None})
    return dict(routed=bool(heads), head_openers=list(dict.fromkeys(heads)),
                head_call_count=len(heads), frames_used=sorted(frames), routed_frame_count=len(frames),
                direction_program=('single_frame' if len(frames) == 1 else 'multi_frame' if len(frames) > 1
                                   else 'unknown_frames' if heads else 'no_head_call'), routed_calls=enriched)


def cells(records):
    def cell(rows):
        n = len(rows)
        return dict(count=n, accuracy=sum(r.get('score', 0.) for r in rows)/n if n else None,
                    route_rate=sum(r.get('routed', False) for r in rows)/n if n else None,
                    parse_failures=sum(r.get('parse_failed', True) for r in rows),
                    errors=sum(r.get('status') != 'complete' for r in rows))
    result = {}
    for kind in TYPES:
        rows = [r for r in records if r['question_type'] == kind]
        entry = {**cell(rows), 'by_source': {s: cell([r for r in rows if r['dataset'] == s]) for s in SOURCES}}
        if 'direction' in kind:
            entry['by_program'] = {p: cell([r for r in rows if r.get('direction_program') == p])
                                   for p in ('single_frame', 'multi_frame', 'unknown_frames', 'no_head_call')}
        result[kind] = entry
    return dict(per_type=result, by_source={s: cell([r for r in records if r['dataset'] == s]) for s in SOURCES})


def verify_source(request):
    from pathlib import Path
    import student_pilot
    from student_pilot import p3_provenance as p, carrier_c1_run as trainer
    from .runtime import verify_trainer
    spec = request['routed_trainer']
    verify_trainer(spec)
    root = Path(student_pilot.__file__).resolve().parent.parent
    from .items import sha256
    inventory = p.load(p.pinned(spec['inventory']))
    if inventory != {str(f.relative_to(root)): sha256(f) for f in root.rglob('*') if f.is_file()}:
        raise ValueError('Routed trainer inventory differs')
    seal = p.load(p.pinned(request['cfg']['code']))
    if seal.get('clean') is not True or seal.get('commit') != spec['commit'] or seal.get('sources') != spec['closure']:
        raise ValueError('Config trainer closure differs')
    actual = {str(f.relative_to(root)): sha256(f) for f in p.source_files([Path(trainer.__file__)])}
    if actual != spec['closure']:
        raise ValueError('Runtime code closure differs')


def comparison_protocol(request):
    from pathlib import Path
    from .items import sha256
    dev = request.get('preset') == 'routed_dev'
    spec = next(d for d in request['datasets'] if d['benchmark'] == ('routed_dev' if dev else 'official5130'))
    from .routed_dev import TYPES as DEV_TYPES
    result = dict(protocol=request['routed_protocol'], membership=spec['rows']['sha256'], types=list(DEV_TYPES if dev else TYPES),
                greedy=True, enable_thinking=True, max_new_tokens=16384,
                frame_layout=request['cfg']['frame_layout'], frame_markers=request['cfg'].get('frame_markers', False),
                placement=request['cfg']['carrier_placement'],
                snapshot_manifest=request['snapshot_manifest']['sha256'],
                trainer_encoding={n:request['routed_trainer']['sources'][n] for n in
                    ('carrier_c1_canary.py','carrier_c1_data.py','batches.py','pose_samples.py','trace_contract.py')},
                evaluator={n:sha256(Path(__file__).with_name(n)) for n in
                    ('official.py','sampling.py','items.py','routed_types.py')},
                decode_sha256=request['routed_trainer']['sources']['carrier_c1_decode.py'])
    if dev:
        result.update(preset='routed_dev', selection=spec['selection'], parity='dev-two-v1',
                      dev_evaluator=sha256(Path(__file__).with_name('routed_dev.py')))
    if 'pose_override' in request:
        result['pose_override'] = {**request['pose_override'], 'gravity_source': 'student',
                                   'evaluator_sha256': sha256(Path(__file__).with_name('pose_override.py'))}
    return result
