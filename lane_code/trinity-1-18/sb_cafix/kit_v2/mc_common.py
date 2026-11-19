"""Shared paths, pins, RLE and JSON I/O for the mask carry kit (spec in/v2/KIT_SPEC_mask_carry_v2.md).
Every input lives on local /scratch."""
import gzip, hashlib, json, sys, time
from pathlib import Path
import numpy as np

KIT = Path(__file__).resolve().parent
ROOT = KIT.parent
OUT = ROOT/'out'/'v2'
WORK = ROOT/'work'/'v2'
SPEC = ROOT/'in/v2/KIT_SPEC_mask_carry_v2.md'
SPEC_SHA256 = 'a98f18f8730665444e8b5a44ee121023da8a324ed05d660461ae674e0dc93028'
BOX = Path('/scratch/jjyeung/orch_n30/sb_kbox4')
MASKFAIL = Path('/scratch/jjyeung/orch_n30/sb_maskfail')
PHRASE_KIT = Path('/scratch/jjyeung/orch_n30/sb_mask_phrase/kit.py')
# The phrase fix lane's file wins when it exists (same policies); seeds record which file and sha256 they read.
PHRASE_FOLDS_CANDIDATES = (Path('/scratch/jjyeung/orch_n30/sb_phfix/out/PHRASE_FOLDS.json'),
                           Path('/scratch/jjyeung/orch_n30/sb_mask_phrase/out/PHRASE_FOLDS.json'))
PHRASE_FOLDS = next((p for p in PHRASE_FOLDS_CANDIDATES if p.exists()), PHRASE_FOLDS_CANDIDATES[-1])
POPULATION = OUT/'POPULATION.json'
BARS_AMENDMENT = OUT/'BARS_AMENDMENT.json'
RULING = ROOT/'in/RULING_1056Z.md'
VNICE = KIT/'vendor/vnice.sh'
VENDOR_SHA256 = {'vnice.sh': '3ab2b542726f32dbecdbe30104f903aa2bef3526a9257013fd5f8bcc99461c6b',
                 'terminator.sh': '19727987d5517c0e2549e1205e55f4bcc87f34dafe66c96bdf90233305942e5d'}
REUSE = Path('/scratch/jjyeung/orch_n30/sb_kobj4/out/object_route/K1_TRACK.json')
SAM3_ROOT = Path('/scratch/jjyeung/b01ec87a6f29b/d/s')
CHECKPOINT = Path('/scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt')
CHECKPOINT_SHA256 = '9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e'
CHECKPOINT_BYTES = 3450062241
RECEIPT = Path('/scratch/jjyeung/b01ec87a6f29b/d/k/SAM3_RECEIPT.json')
VENDOR_RECEIPT = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam/vendor/SAM3_RECEIPT.json')
TOWER = VENDOR_RECEIPT.parent/'sam3_tower.py'
ROWSET = Path('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt')
CANVAS = (480, 640)
SEED_SETS = ('S_A0', 'S_GT', 'S_PHR')
FRAME_SETS = ('D64', 'A32')
# Registered order of the tracker pass (S_A0/D64, S_GT/D64, A32, S_PHR); trailing sets are dropped first.
ORDER = ['S_A0/D64', 'S_GT/D64', 'S_A0/A32', 'S_GT/A32', 'S_PHR/D64', 'S_PHR/A32']
SEED = 20261119
PINS = {}


def local(path):
    p = Path(path)
    if not str(p.resolve()).startswith('/scratch/'):
        raise PermissionError('local /scratch input required: '+str(p))
    return p


def sha256_file(path):
    h = hashlib.sha256()
    with local(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    p = local(path)
    data = p.read_bytes()
    PINS[str(p)] = hashlib.sha256(data).hexdigest()
    return data


def pin(path):
    value = PINS[str(local(path))] = sha256_file(path)
    return value


def read_json(path):
    data = read(path)
    return json.loads(gzip.decompress(data) if str(path).endswith('.gz') else data)


def frame_sets():
    """out/FRAME_SETS.json with its captures keyed by canonical name."""
    raw = read_json(OUT/'FRAME_SETS.json')
    return dict(raw, captures={c['capture']: c for c in raw['captures']})


def clean(v):
    if isinstance(v, np.ndarray):
        return clean(v.tolist())
    if isinstance(v, np.generic):
        return clean(v.item())
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [clean(x) for x in v]
    if isinstance(v, float) and not np.isfinite(v):
        return None
    return v


def all_pins():
    pins = dict(PINS)
    ladder = sys.modules.get('dryrun')
    if ladder is not None and hasattr(ladder, 'PINS'):
        pins.update(ladder.PINS)
    return dict(sorted(pins.items()))


def code_pins():
    for p in sorted(KIT.glob('*.py')) + sorted(KIT.glob('*.sh')) + sorted(KIT.glob('vendor/*.sh')):
        read(p)


def dataset(canonical):
    return canonical.split('/', 1)[0]


def population_digest(body):
    """Content id of a population: the decision and beside capture and row lists plus the tracking order."""
    keys = ('decision', 'beside', 'track_order')
    text = json.dumps({k: body[k] for k in keys}, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(text.encode()).hexdigest()


def population():
    """out/v2/POPULATION.json (RULING 1056Z), refused when its content no longer matches its population_id."""
    raw = read_json(POPULATION)
    if population_digest(raw) != raw['population_id']:
        raise ValueError('POPULATION.json content differs from its population_id')
    return raw


def write_json(path, obj, gz=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(clean(dict(obj, input_sha256=all_pins())), allow_nan=False, separators=(',', ':') if gz else None, indent=None if gz else 1)
    tmp = path.with_name(path.name+'.tmp')
    if gz:
        tmp.write_bytes(gzip.compress(text.encode(), 6))
    else:
        tmp.write_text(text+'\n')
    tmp.replace(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def status(text):
    """Append to out/v2/STATUS_LOG.md and rewrite STATUS.md with the whole v2 history."""
    stamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT/'STATUS_LOG.md').open('a') as f:
        f.write(f'- {stamp} {text}\n')
    head = '# STATUS (sb_cafix: kit_v2/, out/v2/)\n\n'
    (ROOT/'STATUS.md').write_text(head+(OUT/'STATUS_LOG.md').read_text())


def stub(canonical):
    return canonical.replace('/', '__')


def rle_encode(mask):
    """Column-major run lengths starting with background, the stage-1 cache format."""
    m = np.asarray(mask, bool)
    flat = m.reshape(-1, order='F')
    bounds = np.concatenate([[0], np.flatnonzero(flat[1:] != flat[:-1])+1, [flat.size]])
    runs = np.diff(bounds)
    if flat.size and flat[0]:
        runs = np.concatenate([[0], runs])
    return dict(size=list(m.shape), counts=[int(x) for x in runs])


def rle_decode(rle):
    counts = np.asarray(rle['counts'], np.int64)
    h, w = rle['size']
    if np.any(counts < 0) or counts.sum() != h*w:
        raise ValueError('invalid_rle')
    return np.repeat(np.arange(len(counts)) % 2 == 1, counts).reshape((h, w), order='F')


def pack(masks):
    masks = np.asarray(masks, bool)
    return dict(shape=list(masks.shape), bits=np.packbits(masks.reshape(-1)))


def unpack(shape, bits):
    n = int(np.prod(shape))
    return np.unpackbits(np.asarray(bits, np.uint8), count=n).astype(bool).reshape(shape)


def iou(a, b):
    a = np.asarray(a, bool); b = np.asarray(b, bool)
    union = np.count_nonzero(a | b)
    return np.count_nonzero(a & b)/union if union else None


def nearest(mask, shape):
    """Nearest-neighbour resize by index sampling; matches ndimage.zoom(order=0) only when the ratio is an integer."""
    mask = np.asarray(mask)
    h, w = mask.shape
    rows = np.minimum((np.arange(shape[0])+.5)*h/shape[0], h-1).astype(int)
    cols = np.minimum((np.arange(shape[1])+.5)*w/shape[1], w-1).astype(int)
    return mask[rows][:, cols]
