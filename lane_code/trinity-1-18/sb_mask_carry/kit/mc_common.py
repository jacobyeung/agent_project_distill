"""Shared paths, pins, RLE and JSON I/O for the mask carry kit. Every input lives on local /scratch."""
import gzip, hashlib, json, sys, time
from pathlib import Path
import numpy as np

KIT = Path(__file__).resolve().parent
ROOT = KIT.parent
OUT = ROOT/'out'
WORK = ROOT/'work'
BOX = Path('/scratch/jjyeung/orch_n30/sb_kbox4')
MASKFAIL = Path('/scratch/jjyeung/orch_n30/sb_maskfail')
PHRASE_SET = Path('/scratch/jjyeung/orch_n30/sb_mask_phrase/out/PHRASE_SET.json')
PHRASE_PART2 = Path('/scratch/jjyeung/orch_n30/sb_mask_phrase/out/pool_part2')
REUSE = Path('/scratch/jjyeung/orch_n30/sb_kobj4/out/object_route/K1_TRACK.json')
SAM3_ROOT = Path('/scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src')
CHECKPOINT = Path('/scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt')
CHECKPOINT_SHA256 = '9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e'
RECEIPT = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam/vendor/SAM3_RECEIPT.json')
TOWER = RECEIPT.parent/'sam3_tower.py'
CANVAS = (480, 640)
SEED_SETS = ('S_A0', 'S_GT', 'S_PHR')
FRAME_SETS = ('D64', 'A32')
# Registered order of the tracker pass; trailing sets are dropped first.
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
    for p in sorted(KIT.glob('*.py')) + sorted(KIT.glob('*.sh')):
        read(p)


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
    stamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    with open(ROOT/'STATUS.md', 'a') as f:
        f.write(f'- {stamp} {text}\n')


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
    return np.packbits(np.asarray(masks, bool).reshape(-1))


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
