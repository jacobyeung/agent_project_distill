"""CPU utilities and fixed TOWER-0 inference contract."""
import ast
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import sys
from functools import lru_cache

import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
EVAL = Path('/scratch/jjyeung/orch_cd/evalx/work')
TOOL = Path('/scratch/jjyeung/orch_cd/toolprog/work')
GT_ROOT = TOOL / 'gt/scannet'
DEV_SCENES = EVAL / 'devpool/DEV_SCENES.json'
DEV_ITEMS = EVAL / 'devpool/DEV_GROUND_ITEMS.jsonl'
POINTING = EVAL / 'aws_vl/inputs/pointing_membership.json'
GROUND = EVAL / 'devpool/GROUND_MEMBERSHIP.json'
CHECKPOINT = WORK / 'sam3_weights/sam3.pt'
CONTRACT = {
    'version': 1, 'phrase_rule': 'lowercase, underscores to spaces, collapse whitespace; fixed singular exceptions',
    'instance_floor': .3, 'max_instances': 5, 'mask_threshold': .5,
    'accept': 'presence * highest independent instance probability >= tau; nonempty top mask required',
    'click': 'argmax padded Euclidean distance transform; first row-major tie; pixel-center canvas',
    'resolution': 1008, 'precision': 'bf16 autocast', 'mode': 'image; one backbone per frame',
    'tau_objective': 'max min(visible eroded-mask hit rate, frame-absent explicit-null rate)',
    'tau_tie': 'highest threshold', 'split': 'agg.tune_scene(bare scene name) AND development membership',
    'training_labels': False,
}
SINGULAR = {'kitchen cabinets': 'kitchen cabinet', 'cabinets': 'cabinet', 'chairs': 'chair',
            'tables': 'table', 'doors': 'door', 'windows': 'window', 'shelves': 'shelf',
            'bookshelves': 'bookshelf', 'desks': 'desk', 'beds': 'bed', 'sofas': 'sofa',
            'couches': 'couch', 'curtains': 'curtain', 'blinds': 'window blind',
            'books': 'book', 'pillows': 'pillow', 'lamps': 'lamp', 'boxes': 'box',
            'pictures': 'picture', 'towels': 'towel', 'clothes': 'clothing',
            'clothes dryers': 'clothes dryer', 'pipes': 'pipe'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path, limit=64*1024*1024):
    path = Path(path)
    if path.stat().st_size > limit:
        raise ValueError(f'Metadata exceeds {limit} bytes: {path}')
    return json.loads(path.read_text())


def dump(path, value, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x' if exclusive else 'w') as f:
        f.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def load_module(name, path):
    sys.path.insert(0, str(Path(path).parent))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=None)
def tune_scene(scene):
    # Reuse the exact function used by agg_experiment, without importing its runners.
    path = EVAL / 'tp/agg.py'
    tree = ast.parse(path.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'tune_scene')
    ns = {'hashlib': hashlib}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), ns)
    return ns['tune_scene'](scene.split('/')[-1])


def tuning_scenes():
    return {'scannet/' + s for s in read_json(DEV_SCENES)['scenes'] if tune_scene(s)}


def phrase(label):
    label = ' '.join(label.lower().replace('_', ' ').split())
    return SINGULAR.get(label, label)


def phrase_map(labels):
    return {label: phrase(label) for label in sorted(set(labels))}


def fixed_sha():
    return digest({'contract': CONTRACT, 'singular': SINGULAR})


def require_frozen(path=HERE/'tau_frozen.json'):
    if not Path(path).is_file():
        raise RuntimeError('tau_frozen.json is required BEFORE reading held-out items')
    frozen = read_json(path)
    if frozen.get('contract_sha256') != fixed_sha():
        raise RuntimeError('Frozen tower contract differs; do not read held-out items')
    if frozen.get('inputs', {}).get('dev_scenes') != sha(DEV_SCENES):
        raise RuntimeError('Development scene membership differs from frozen inputs')
    if frozen.get('inputs', {}).get('dev_items') != sha(DEV_ITEMS):
        raise RuntimeError('Development items differ from frozen inputs')
    if not np.isfinite(frozen.get('tau', np.nan)) or not frozen.get('tuning_scenes'):
        raise RuntimeError('Invalid frozen threshold')
    for name, expected in frozen.get('implementation_sha256', {}).items():
        if sha(HERE/name) != expected:
            raise RuntimeError(f'Frozen implementation differs: {name}')
    for path_key, source in [('gt_programs', TOOL/'tp/programs.py'), ('split_function', EVAL/'tp/agg.py')]:
        if frozen['inputs'].get(path_key) != sha(source):
            raise RuntimeError(f'Frozen source differs: {source}')
    return frozen


def normalize_item(it):
    scene = it.get('scene', it.get('scene_key'))
    if '/' not in scene:
        scene = 'scannet/' + scene
    frame = int(it['frame'])
    if not 1 <= frame <= 32:
        raise ValueError('Frame must be a 1-based anchor')
    return dict(id=str(it['id']), scene=scene, frame=frame, obj=it['obj'], kind=it.get('kind', 'point'))


def tuning_items():
    allowed = tuning_scenes()
    if DEV_ITEMS.stat().st_size > 16*1024*1024:
        raise ValueError('Development item bound exceeded')
    result = []
    with DEV_ITEMS.open() as f:
        for line in f:
            key = re.search(r'"scene_key"\s*:\s*"([^"\\]+)"', line)
            if key is None:
                raise ValueError('Development item lacks a plain scene_key')
            if key.group(1) not in allowed:
                continue
            it = json.loads(line)
            # Parse object/frame fields only after the tuning-scene filter.
            if it['scene_key'] in allowed and it['kind'] == 'point':
                result.append(normalize_item(it))
    return result


def membership(path):
    require_frozen()
    value = read_json(path)
    rows = value['items'] if isinstance(value, dict) else value
    return [normalize_item(it) for it in rows if it.get('kind', 'point') == 'point']


def deepest(mask):
    mask = np.asarray(mask, dtype=bool)
    if mask.ndim != 2 or not mask.any():
        return None
    try:
        from scipy.ndimage import distance_transform_edt
        dt = distance_transform_edt(np.pad(mask, 1))[1:-1, 1:-1]
    except ImportError:
        import cv2
        dt = cv2.distanceTransform(np.pad(mask, 1).astype(np.uint8), cv2.DIST_L2,
                                   cv2.DIST_MASK_PRECISE)[1:-1, 1:-1]
    y, x = np.unravel_index(int(dt.argmax()), mask.shape)
    h, w = mask.shape
    return [float((x + .5) / w * 1000), float((y + .5) / h * 1000)]


def rle_encode(mask):
    """Uncompressed COCO RLE: column-major, zero run first."""
    mask = np.asarray(mask, dtype=bool)
    a = mask.ravel(order='F').astype(np.uint8)
    changes = np.flatnonzero(np.diff(a)) + 1
    counts = np.diff(np.r_[0, changes, a.size]).tolist()
    if a.size and a[0]:
        counts.insert(0, 0)
    return {'size': list(mask.shape), 'counts': counts}


def rle_decode(rle):
    counts = np.asarray(rle['counts'], dtype=np.int64)
    if (counts < 0).any() or int(counts.sum()) != int(np.prod(rle['size'])):
        raise ValueError('Invalid RLE')
    return np.repeat(np.arange(len(counts)) % 2, counts).astype(bool).reshape(rle['size'], order='F')


def response(point):
    return json.dumps([{'point_2d': point}], allow_nan=False)


def accepted(record, tau):
    return bool(record['instances'] and record['click'] is not None and record['joint_score'] >= tau)


def cache_path(raw, scene):
    return Path(raw) / (scene.replace('/', '__') + '.npz')


def save_cache(path, value):
    # Atomic replacement; incomplete tmp files are preserved, never deleted.
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.partial.npz')
    np.savez_compressed(tmp, payload=np.frombuffer(canonical(value).encode(), dtype=np.uint8))
    tmp.replace(path)


def load_cache(raw, scene):
    path = cache_path(raw, scene)
    with np.load(path, allow_pickle=False) as z:
        value = json.loads(z['payload'].tobytes())
    if value['contract_sha256'] != fixed_sha() or value['scene'] != scene:
        raise ValueError(f'Cache contract mismatch: {path}')
    return value


def lookup(cache, frame, label):
    return cache['frames'][str(frame-1)]['phrases'][phrase(label)]


@lru_cache(maxsize=1)
def scorer():
    # Both projects name a utility module common.py. Bind the scorer to its own.
    original = sys.modules.get('common')
    sys.modules['common'] = load_module('_evalx_common', EVAL/'aws_vl/local/common.py')
    try:
        return load_module('_tower_score', EVAL/'aws_vl/local/score_pointing.py')
    finally:
        if original is not None:
            sys.modules['common'] = original
        else:
            sys.modules.pop('common', None)


@lru_cache(maxsize=1)
def video_scorer():
    sys.modules['score_pointing'] = scorer()
    original = sys.modules.get('common')
    sys.modules['common'] = load_module('_evalx_common_video', EVAL/'aws_vl/local/common.py')
    try:
        return load_module('_tower_video_score', EVAL/'aws_vl/local/score_pointing_video.py')
    finally:
        if original is not None:
            sys.modules['common'] = original
        else:
            sys.modules.pop('common', None)


def gt(scene):
    score = scorer()
    return score.ground(scene, GT_ROOT, score.programs())


def make_row(it, text):
    parsed = json.loads(text)
    point = parsed[0]['point_2d'] if isinstance(parsed, list) else parsed['point_2d']
    return dict(benchmark='pointing', example_id=it['id'], scene=it['scene'], frame=it['frame'],
                obj=it['obj'], status='complete', raw_generation=text, response_text=text,
                hit_token_cap=False, output_tokens=0, model='sam3-zero-shot', inference_only=True,
                accepted_presence=point is not None)


def journal(path, rows):
    with Path(path).open('w') as f:
        for row in rows:
            f.write(canonical(row) + '\n')
