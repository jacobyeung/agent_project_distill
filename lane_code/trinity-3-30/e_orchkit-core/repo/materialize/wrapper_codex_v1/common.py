from __future__ import annotations
import hashlib, importlib, json, os, re, socket, sys, time, uuid
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
from functools import lru_cache
ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / 'CONFIG.json').read_text())
PACKAGE = Path(CONFIG['package'])
CONTRACT = Path(CONFIG['source_contract']['path'])
CONTRACT_SHA = CONFIG['source_contract']['sha256']
PREPARER_SHA = 'ba5bef689dafdafa7d2c52f447315269f144c136099a4057527bb8c29dd5e901'
COORD = Path(CONFIG['coord_root'])
OWNER = CONFIG['owner']
PYTHON = CONFIG['python']
JOBS = Path(CONFIG['jobs_root'])
READY = Path(CONFIG['ready_root'])
ENV = CONFIG['environment']
sys.path.insert(0, str(PACKAGE))


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text())


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def digest_value(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def pin(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f'not a regular non-symlink file: {path}')
    return {'path': str(path.resolve()), 'sha256': sha(path), 'size_bytes': path.stat().st_size}


def verify_pin(spec):
    require(pin(spec['path']) == spec, f'pin drift: {spec["path"]}')
    return Path(spec['path'])


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def host():
    return socket.gethostname().split('.')[0]


def identity(pid=None):
    pid = os.getpid() if pid is None else int(pid)
    base = Path('/proc') / str(pid)
    text = (base / 'stat').read_text()
    fields = text[text.rindex(')') + 2:].split()
    return {'host': host(), 'pid': pid, 'uid': base.stat().st_uid,
            'start_ticks': int(fields[19]), 'state': fields[0],
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'argv': (base / 'cmdline').read_bytes().replace(b'\x00', b' ').decode(errors='replace').strip()}


def same_process(expected):
    try:
        actual = identity(expected['pid'])
    except (FileNotFoundError, ProcessLookupError):
        return False
    return all(actual[k] == expected[k] for k in ('host', 'pid', 'uid', 'start_ticks', 'boot_id')) and actual['state'] != 'Z'


def verify_sources():
    require(sha(CONTRACT) == CONTRACT_SHA, 'reviewed source contract drift')
    contract = read_json(CONTRACT)
    require(contract['source_root'] == str(PACKAGE), 'source root drift')
    require(len(contract['source_files']) == 40, 'source file count drift')
    actual = {name: sha(PACKAGE / name) for name in contract['source_files']}
    mismatches = [name for name, value in actual.items() if value != contract['source_files'][name]]
    require(not mismatches, f'SOURCE_DRIFT: {mismatches}; hold for parent/teacher')
    require(actual['prepare_gt_scene.py'] == PREPARER_SHA, 'preparer identity drift')
    if str(PACKAGE) not in sys.path:
        sys.path.insert(0, str(PACKAGE))
    checked = importlib.import_module('audit_package').verify_contract(CONTRACT, CONTRACT_SHA)
    require(checked['source_files'] == actual, 'reviewed source validator disagrees')
    return {'checked_at': utc(), 'contract': pin(CONTRACT), 'source_files': actual, 'count': len(actual)}


def convention(inspection, expected):
    import numpy as np
    require(expected in ('full', 'half'), 'unknown authorized OBB convention')
    require(inspection['association'] in ('face_segIndices', 'vertex_segIndices_all_three_vertices_agree'), 'ambiguous mesh association')
    supported = [row for row in inspection['instances'] if row['face_count'] > 0]
    require(len(supported) >= 3, 'insufficient mesh witnesses for OBB convention')
    values = np.asarray([row['max_axis_ratio_to_source_axesLengths'] for row in supported], dtype=np.float64)
    require(values.shape == (len(supported), 3) and np.isfinite(values).all() and (values >= 0).all(), 'invalid per-instance ratios')
    candidates = []
    for name, factor in (('full', 0.5), ('half', 1.0)):
        if np.all(values <= factor * 1.05) and np.all(values.max(axis=1) >= factor * 0.95) and np.allclose(np.median(values, axis=0), factor, rtol=0.001, atol=0.0001):
            candidates.append(name)
    require(candidates == [expected], f'AMBIGUOUS_OR_DIFFERENT_OBB: witnessed={candidates}, authorized={expected}; parent decision required')
    require(len(inspection['instances']) == inspection['segGroups'], 'diagnostic instance count drift')
    return {'convention': expected, 'factor': 0.5 if expected == 'full' else 1.0,
            'supported_instances': len(supported), 'zero_face_instances': len(inspection['instances']) - len(supported),
            'axis_median': np.median(values, axis=0).tolist(), 'axis_max': values.max(axis=0).tolist(),
            'rule': 'Every supported instance reaches95% of the candidate half-axis; all axes remain within the reviewed105% containment bound; per-axis medians match one fixed convention within0.1%. No calibration is fitted.'}


def membership_summary(rows):
    return {'question_count': len(rows), 'qids': [r['id'] for r in rows],
            'taskmix': dict(sorted(Counter(r['question_type'] for r in rows).items())),
            'source_taskmix': dict(sorted(Counter(r['source_question_type'] for r in rows).items())),
            'exact_rows_sha256': digest_value(rows)}

def write(path, value, *, replace=False):
    path = Path(path)
    require(any(path.resolve().is_relative_to(r.resolve()) for r in (ROOT,JOBS,READY)), f'write outside namespace: {path}')
    require(not path.is_symlink(), 'symlink output')
    payload = value.encode() if isinstance(value,str) else canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f'.{path.name}.{uuid.uuid4().hex}.private'
    with temporary.open('xb') as handle:
        handle.write(payload); handle.flush(); os.fsync(handle.fileno())
    if replace:
        os.replace(temporary,path)
    else:
        os.link(temporary,path)
    fsync_dir(path.parent)
    return pin(path)

publish = write

def work_id(scene):
    require(bool(re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*',scene)), 'unsafe scene')
    return f'preprocess__req232_gt_scene_{scene}__train50k__s17__76e67ed6e8'

def parse_plan(plan,census):
    duplicates = {s['scene'] for s in census['scenes'] if s['conflicting_memberships'] > 0}
    known = {s['scene'] for s in census['scenes']}
    scenes=plan['scenes']
    require(len(scenes)==plan['scene_count'] and len({s['scene'] for s in scenes})==len(scenes),'plan scene census mismatch')
    require(sum(s['question_count'] for s in scenes)==plan['question_count'],'plan question census mismatch')
    result=[]
    for source in scenes:
        s=dict(source); work_id(s['scene'])
        require(s['work_id']==work_id(s['scene']),'plan work id mismatch')
        require(len(s['qids'])==len(set(s['qids']))==s['question_count'],'qid census mismatch')
        if s['dataset']=='scannet': blocker='unsupported_scannet_adapter'
        elif s['dataset']=='scannetppv2':
            require(s['scene'] in known,'scene missing membership census')
            blocker='overlapping_instance_membership' if s['scene'] in duplicates else None
        else: raise ValueError('unknown dataset')
        s['blocking_class']=blocker
        result.append(s)
    return result

@lru_cache(maxsize=1)
def load_plan():
    for key in ('plan','duplicate_census','refusal_taxonomy'):
        verify_pin(CONFIG[key])
    rows=parse_plan(read_json(CONFIG['plan']['path']),read_json(CONFIG['duplicate_census']['path']))
    require(len(rows)==385 and sum(r['blocking_class'] is None for r in rows)==93,'expected 385/93 scope mismatch')
    return rows

@lru_cache(maxsize=1)
def all_rows():
    from training_assets import teacher_rows
    return teacher_rows()

def selected_rows(scene):
    rows=[r for r in all_rows() if r['dataset']=='scannetppv2' and r['scene_name']==scene]
    plan=next((r for r in load_plan() if r['scene']==scene),None)
    if plan is None:
        require(scene==CONFIG['dry_scene'],'scene outside scope')
        plan=CONFIG['dry_plan']
    require(len(rows)==plan['question_count'] and [r['id'] for r in rows]==plan['qids'],'exact plan membership mismatch')
    return rows

def scene_plan(scene, dry=False):
    if dry:
        require(scene==CONFIG['dry_scene'],'invalid dry scene')
        s=dict(CONFIG['dry_plan']); job=ROOT/'dry_run'
    else:
        s=dict(next(r for r in load_plan() if r['scene']==scene))
        require(s['blocking_class'] is None,'blocked scene cannot execute')
        job=JOBS/scene
    s.update(membership_summary(selected_rows(scene)))
    s.update(output=str(job/'assets'),inspection=str(job/'INSPECTION.json'),runtime_scene_id='scannetppv2__'+scene)
    return s

def require_env():
    for key,value in ENV.items():
        require(os.environ.get(key)==value,f'environment mismatch: {key}')
    require(host() in CONFIG['host_caps'],'host outside pinned configuration')
    require(Path.cwd()==ROOT,'wrong wrapper cwd')

def verify_scripts():
    seal=read_json(ROOT/'CONTRACT.json')
    require(set(seal['files'])==set(CONFIG['closure_files']),'wrapper closure census drift')
    for name,spec in seal['files'].items():
        require(Path(spec['path'])==ROOT/name,'wrapper path drift'); verify_pin(spec)
    for spec in seal['inputs'].values(): verify_pin(spec)
    require(seal['source_contract_sha256']==CONTRACT_SHA,'source contract mismatch')
    return pin(ROOT/'CONTRACT.json')

def lease(scene):
    value=read_json(COORD/'LEASES'/(work_id(scene)+'.lock')/'lease.json')
    require(value['agent_id']==OWNER and value['work_id']==work_id(scene),'foreign lease')
    age=(datetime.now(timezone.utc)-datetime.fromisoformat(value['last_heartbeat'])).total_seconds()
    require(value['status'] in ('running','claimed') and 0<=age<1800,'lease stale or terminal')
    return value

def registry(receipts):
    return {'schema':'r1313-assets-registry-v1','round':1313,'receipts':receipts}
