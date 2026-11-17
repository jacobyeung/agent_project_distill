"""Canonical, immutable evaluation membership and reserve-room checks."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from student_pilot.h1_r0 import Reserve, room_key, R0_SHA256

K = Path(__file__).resolve().parents[1]
ROOT = Path('/scratch/jjyeung/orch_n30')
R0 = K/'auth/R0_ROOMS.txt'
REVSI = K/'items_sources/revsi999.json'
DIRECT = K/'items_sources/e193_items.json'
TASKS = K/'items_sources/TASKS.jsonl'
CAMERA = K/'items_sources/CAMERA_TASKS.jsonl'
CAMERA_SHA = 'f59090ffc8fd0f4d80a2b049e2624660c0f46dbc1d26016145f4747850a432ac'
TASKS_SHA = 'a2f3fdbdab06ab81942d44044d85090df8ec5b86908cf010cdbcb17e35637f5e'

def portable_pin(path):
    p = Path(path).resolve()
    return dict(path=str(p.relative_to(K)) if p.is_relative_to(K) else str(p), sha256=sha(p))

def resolve_pin(value):
    p = Path(value['path'])
    return {**value, 'path':str(p if p.is_absolute() else K/p)}

def checked(path, expected):
    if sha(path) != expected:raise ValueError('Source SHA256 mismatch: '+str(path))
    return path


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def pin(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def read_items(path):
    p = Path(path)
    if p.suffix == '.jsonl':
        return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
    data = json.loads(p.read_text())
    return data if isinstance(data, list) else data['items']


def canonical(items):
    result = []
    for raw in items:
        item = dict(raw)
        item['id'] = str(item.get('id', item.get('example_id', item.get('qid', ''))))
        if not item['id']:
            raise ValueError('Missing item id')
        item['room_key'] = room_key(item)
        result.append(item)
    result.sort(key=lambda r: r['id'])
    if len({r['id'] for r in result}) != len(result):
        raise ValueError('Duplicate item ids')
    return result


def manifest(name, items, source, *, extra_sources=(), r0=None):
    items = canonical(items)
    reserve = Reserve(r0 or dict(path='auth/R0_ROOMS.txt', sha256=R0_SHA256))
    found = sum(reserve.excluded(r) for r in items)
    if name not in ('r0dev','r0dev_f32') and found:
        raise ValueError(f'{name}: {found} items overlap R0; fixed sets cannot be silently filtered')
    if name in ('r0dev','r0dev_f32'):
        dev = set((R0.parent/'R0_DEV_ROOMS.txt').read_text().splitlines())
        if any(r['room_key'] not in dev for r in items):
            raise ValueError('r0dev permits R0_DEV_ROOMS only')
    result = dict(schema='h1-items-v1', name=name, status='ready', source=portable_pin(source),
                sources=[portable_pin(source), *[portable_pin(p) for p in extra_sources]], items=items,
                item_set_sha256=digest(items), count=len(items),
                per_type=dict(sorted(Counter(r['question_type'] for r in items).items())),
                r0_check=dict(pin=reserve.pin, checked=len(items), found=found),
                development_only=name in ('r0dev','r0dev_f32'))
    if name in ('r0dev','r0dev_f32'):result['r0_dev_pin'] = portable_pin(R0.parent/'R0_DEV_ROOMS.txt')
    return result


def load_manifest(path):
    m = json.loads(Path(path).read_text())
    if m.get('status') != 'ready':
        raise ValueError(m.get('reason', 'Item set is not ready'))
    if m.get('schema') != 'h1-items-v1' or digest(m['items']) != m['item_set_sha256']:
        raise ValueError('Item-set hash mismatch')
    if canonical(m['items']) != m['items']:
        raise ValueError('Item list is not canonical')
    reserve = Reserve(m['r0_check']['pin'])
    found = sum(reserve.excluded(r) for r in m['items'])
    if m['count'] != len(m['items']) or m['r0_check']['checked'] != m['count'] or found != m['r0_check']['found']:
        raise ValueError('Item-set R0 coverage differs')
    if m['name'] not in ('r0dev','r0dev_f32') and found:
        raise ValueError('Item set overlaps R0')
    if m['name'] in ('r0dev','r0dev_f32'):
        if sha(resolve_pin(m['r0_dev_pin'])['path']) != m['r0_dev_pin']['sha256']:
            raise ValueError('R0-dev pin mismatch')
        dev = set((Path(resolve_pin(reserve.pin)['path']).parent/'R0_DEV_ROOMS.txt').read_text().splitlines())
        if any(r['room_key'] not in dev for r in m['items']):
            raise ValueError('Item outside R0-dev')
    if m['name']=='r0dev_f32':
        if not m.get('development_only'):raise ValueError('R0-dev must remain development only')
        expected=build_r0dev()
        for key in ('item_set_sha256','sources','constants','frames_manifest_sha256','per_type','count','source'):
            if m[key]!=expected[key]:raise ValueError('R0-dev pinned '+key+' differs')
    return m


def build(out=K/'items', *, routed=None, direct_tasks=None, forward_tasks=None, away_tasks=None, r0dev=None, sets=None):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    results = {}
    for name in sets or ('revsi999', 'devs1_routed', 'devs1_direct_main', 'devs1_direct', 'r0dev'):
        try:
            if name == 'revsi999':
                rows = read_items(REVSI)
                counts = Counter(r.get('category', r['question_type']) for r in rows)
                if len(rows) != 999 or counts['object_abs_distance'] != 283 or counts['room_size_estimation'] != 37:
                    raise ValueError('revsi999 type counts differ')
                if any('in meters' not in r['question'].lower() for r in rows if r['question_type'] == 'object_abs_distance'):
                    raise ValueError('revsi distance unit differs')
                value = manifest(name, rows, REVSI)
            elif name == 'devs1_routed':
                if routed is None:
                    cameras = read_items(checked(CAMERA, CAMERA_SHA))
                    main = read_items(checked(TASKS, TASKS_SHA))
                    rows = cameras + [r for r in main if r['question_type'] in ('object_abs_distance','room_size_estimation')]
                    sources = [TASKS]
                    source = CAMERA
                else:
                    rows = read_items(routed)
                    source, sources = routed, []
                expected = {t:150 for t in ('camera_displacement','camera_movement_direction','camera_rotation','object_abs_distance')}
                expected['room_size_estimation'] = 36
                if Counter(r['question_type'] for r in rows) != expected:
                    raise ValueError('devs1_routed requires the fixed 636 items (150/150/150/150/36)')
                inventory_path = K/'items_sources/c8r_inventory.json'
                inventory = json.loads(inventory_path.read_text())
                if {str(r['id']) for r in rows} != set(inventory['keys']):
                    raise ValueError('devs1_routed membership differs from the native C8r read')
                from rows.expected_calls import expected_calls, CAMERA_TYPES
                cameras = [r for r in rows if r['question_type'] in CAMERA_TYPES]
                for r in cameras:
                    call = expected_calls(r['question'], r['question_type'])
                    i,j = r['display_frame_pair']
                    expected_call = f'<{"turn" if r["question_type"]=="camera_rotation" else "move"} from={i} to={j}>'
                    if call != [expected_call]:raise ValueError('Camera question/frame mismatch: '+r['id'])
                value = manifest(name, rows, source, extra_sources=[*sources, inventory_path])
                value['camera_parse'] = dict(checked=len(cameras), parsed=len(cameras), rate=1.)
            elif name in ('devs1_direct', 'devs1_direct_main'):
                checked(DIRECT, '2ab22b681533c48b7a8ba9a78b7d95d1ea78c4d76beb13ad2784d42738f2cbf1')
                inventory = json.loads(DIRECT.read_text())['families']
                # D0 direct families: main, forward, away. Camera belongs to routed.
                expected = {}
                for family in (('main',) if name == 'devs1_direct_main' else ('main','forward','away')):
                    expected.update(inventory[family]['items'])
                main_source = checked(direct_tasks or TASKS,TASKS_SHA)
                rows = read_items(main_source)
                task_sources = [main_source]
                if name == 'devs1_direct':
                    if not forward_tasks or not away_tasks:
                        raise ValueError('300 facing-twin payloads absent: supply --forward-tasks and --away-tasks with native SHA256 pins')
                    for family, payload in [('forward',forward_tasks),('away',away_tasks)]:
                        checked(payload,inventory[family]['tasks_sha256'])
                        rows.extend(read_items(payload));task_sources.append(payload)
                by_id = {str(r.get('example_id', r['id'])): r for r in rows}
                missing = set(expected)-set(by_id)
                if missing:
                    raise ValueError(f'Supply --direct-tasks: {len(missing)} e193 forward/away tasks lack staged room/question payloads')
                rows = [by_id[k] for k in sorted(expected)]
                if any(r['question_type'] != expected[str(r.get('example_id',r['id']))] for r in rows):
                    raise ValueError('e193 item types differ')
                value = manifest(name, rows, DIRECT, extra_sources=task_sources)
            elif name in ('r0dev','r0dev_f32'):
                if r0dev is None and (K/'inputs/r0dev/R0_QUESTIONS_dev_f32.jsonl').exists():
                    value=build_r0dev()
                elif r0dev is None:
                    raise ValueError('Supply --r0dev-items; reserve-development interface is disabled without an item file')
                else:value = manifest(name, read_items(r0dev), r0dev)
            else:
                raise ValueError('Unknown item set: '+name)
        except (ValueError, FileNotFoundError, KeyError) as error:
            value = dict(schema='h1-items-v1', name=name, status='unavailable', reason=str(error))
        path = out/(name+'.json')
        text = json.dumps(value, indent=None if name in ('r0dev','r0dev_f32') else 2, sort_keys=True, separators=(',',':') if name in ('r0dev','r0dev_f32') else None, allow_nan=False)+'\n'
        if path.exists() and json.loads(path.read_text()).get('status') == 'ready' and path.read_text() != text:
            # Only pin relocation is allowed; every pinned digest and item stays identical.
            def without_paths(v):
                if isinstance(v,dict):return {k:without_paths(x) for k,x in v.items() if not (k=='path' and set(v)=={'path','sha256'})}
                if isinstance(v,list):return [without_paths(x) for x in v]
                return v
            if without_paths(json.loads(path.read_text())) != without_paths(value):
                raise ValueError('Refusing to replace pinned manifest: '+str(path))
        path.write_text(text)
        results[name] = {k:v for k,v in value.items() if k != 'items'}
    return results


R0_PINS = {
 'R0_QUESTIONS_dev_f32.jsonl':'b4e278f242e143d8ee66fa527449c7e02fad753bbbb528bd0c31fb9e47aea181',
 'FRAMES_MANIFEST.json':'450e4125b876f0d4dcda514c98ea00aeb852bbf9b273e1c6f3e40f3bc878d496',
 'R0_QUESTIONS_SUMMARY.json':'8444684f62e6110058657de6e33cf2ffb2745a631afd0146bcefc84b10a8ea4f',
 'R0_DEV_ROOMS.txt':'855ef477143a1e6ba7bf4a0a400c718721f54d6337977ad6663ca9a2a3073f58'}


def build_r0dev():
    root=K/'inputs/r0dev'
    for name,h in R0_PINS.items():checked(root/name,h)
    rows=read_items(root/'R0_QUESTIONS_dev_f32.jsonl')
    constants=json.loads((root/'R0_QUESTIONS_SUMMARY.json').read_text())['constants']
    frames=json.loads((root/'FRAMES_MANIFEST.json').read_text())['scenes']
    dev=set((root/'R0_DEV_ROOMS.txt').read_text().splitlines())
    for r in rows:
        key=room_key(r)
        if key not in dev or r['r0_split']!='R0-dev':raise ValueError('Item outside R0-dev')
        f=frames[key]
        if f['deferred'] or f['r0_split']!='R0-dev':raise ValueError('Unadmitted frame room')
        indices=[i*(r['total_num_frames']-1)//31 for i in range(32)]
        if r['num_frames']!=32 or r['frame_indices']!=indices or f['total_frames']!=r['total_num_frames']:
            raise ValueError('R0 frame layout differs')
        r.update(id=r['qid']+'_'+digest(r)[:16],native=key,
                 answer_type='multiple_choice' if r['options'] else 'numeric')
    if len(rows)!=2169 or len({room_key(r) for r in rows})!=98:raise ValueError('R0 item/room count differs')
    if Counter(r['question_type'] for r in rows)!={k:v['n_dev'] for k,v in constants.items()}:
        raise ValueError('R0 per-type counts differ')
    value=manifest('r0dev_f32',rows,root/'R0_QUESTIONS_dev_f32.jsonl',
                   extra_sources=[root/n for n in R0_PINS if n!='R0_QUESTIONS_dev_f32.jsonl'])
    if value['r0_check']['found']!=len(rows):raise ValueError('Training exclusion must cover every development item')
    value.update(constants=constants,frames_manifest_sha256=R0_PINS['FRAMES_MANIFEST.json'])
    return value


def read_contract(manifest, arms, interventions, types=None):
    if manifest['name']=='r0dev_f32':
        if arms!=['own'] or any(m['name']!='none' for m in interventions) or types:
            raise ValueError('R0-dev requires own baseline and all types')
