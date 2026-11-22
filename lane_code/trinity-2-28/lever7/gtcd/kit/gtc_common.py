"""Shared paths, population, frame binding, resize and mask codecs for the GTC-D kit (lane lever7; copy of the GTC-B kit with
arm d added under the GTC-D registration and its lever7 amendment, plan record ROUTED_READER_LEVER_PLAN_20261120).
GTC-D adds arm d: b's seed (the bound GT instance on its largest anchor, lever6/gtcb seeds, bit-identical copies) carried
forward and backward by SAM 3's tracker over the capture's dense frame sequence (dense.py: the VSI-590K mp4 decoded by the
served rule, first..last anchor at the dataset stride plus every anchor), read out at the 32 served anchors.
Read-only inputs: lever6/gtc/out (FRAMES_GTC.json, SEEDS_GTC.json, track/t, track/s, RELIFT_GTC.json) and lever6/gtcb/out
(SEEDS_GTCB.json, seeds/, track/b, RELIFT_GTCB.json).
relift.py is imported from its own path and never copied or edited. Every input is on this node's /scratch.
numpy/stdlib only at import time, so the SAM 3 interpreter can import this module too.
"""
import base64, gzip, hashlib, importlib.util, json, os, sys, time
from pathlib import Path
import numpy as np

KIT = Path(__file__).resolve().parent
ROOT = KIT.parent
OUT = ROOT/'out'                                       # lever7/gtcd/out: arm d only
GTC_OUT = Path('/scratch/jjyeung/orch_n30/lever6/gtc/out')  # read-only GTC outputs (frames index, t and s seeds and tracks)
GTCB_OUT = Path('/scratch/jjyeung/orch_n30/lever6/gtcb/out')  # read-only GTC-B outputs (b seeds, b tracks, RELIFT_GTCB.json)
FRAMES_PATH = GTC_OUT/'FRAMES_GTC.json'
SEEDS_TS = GTC_OUT/'SEEDS_GTC.json'
SEEDS_B_ORIG = GTCB_OUT/'SEEDS_GTCB.json'
SEEDS_B_DIR = OUT/'seeds_b'                            # bit-identical copies of SEEDS_GTCB.json and gtcb/out/seeds/*.npz
SEEDS_B = SEEDS_B_DIR/'SEEDS_GTCB.json'
RELIFT_GTCB = GTCB_OUT/'RELIFT_GTCB.json'
DENSE_ROOT = ROOT/'dense'                              # dense.py output: <dataset>/<capture stub>/<native index>.png
DENSE_MANIFEST = DENSE_ROOT/'DENSE_D.json'
DENSE_SRC = ROOT/'dense_src'                           # governed mp4 streams: <dataset>/<absolute source path>
SUMMARY = ROOT/'lists/SUMMARY.json'                    # phase-1 per-capture sources, strides and dense counts
RELIFT = Path('/scratch/jjyeung/orch_n30/lever5/r1x/r1/relift.py')
DEPTH = Path('/scratch/jjyeung/orch_n30/lever1_c/r1/returned/0.gz')
RECEIPT = Path('/scratch/jjyeung/orch_n30/lever1_c/r1/returned/4.json')  # the 0.gz object receipt (sha256, verified); RETURN_RECEIPT.json is the job receipt and has no top-level verified
ITEMS = Path('/scratch/jjyeung/orch_n30/grd_funnel1/kit/rerun2/items544.json')
META = Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/work/meta/x')
FRAMES_JSON = META/'sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json'
DENSE_JSON = META/'sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json'
# Content-addressed PNG stores (<2 hex>/<sha256>.png); every file is verified against its pinned sha256 on read.
FRAME_ROOTS = (Path('/scratch/jjyeung/devs1_frames'),
               Path('/scratch/jjyeung/orch_n30/nvkey1/work/c0stage/devs1_frames'),
               Path('/scratch/jjyeung/orch_n30/lever5/k5/work/f'))
K1_KIT = Path('/scratch/jjyeung/orch_n30/sb_cachk/kit_v2')
CANVAS = (480, 640)   # served SHAPE in routed_features and K1's tracker video resolution
GRID = (240, 320)     # relift's (32,240,320) cell grid
EXPECTED = dict(items=117, captures=46)
ARMS = ('t', 's')      # the GTC arms, read from GTC_OUT
B_ARMS = ('b',)        # the GTC-B arm, read from GTCB_OUT
D_ARMS = ('d',)        # the GTC-D arm, written under OUT
DATASET_OF = dict(d1='scannet', d2='scannetpp', d3='arkit')   # native prefix -> dense dataset name
STRIDE = dict(scannet=5, scannetpp=24, arkit=2)               # dense stride in native source frames (P1_REPORT)


def seed_copy(seeds_file):
    """The kit's bit-identical copy of a gtcb seeds npz (SEEDS_GTCB.json names the lever6 original)."""
    return SEEDS_B_DIR/Path(seeds_file).name


def dense_indices(anchors, stride):
    """Dense native indices: first..last anchor at the stride (from the first anchor), plus every anchor; sorted."""
    a = [int(x) for x in anchors]
    if a != sorted(a) or len(set(a)) != len(a):
        raise ValueError('anchors must be strictly increasing')
    return sorted(set(range(a[0], a[-1]+1, int(stride))) | set(a))


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def digest(value):
    """h1eval.items.digest: sha256 of canonical JSON (the frame_binding_sha256 producer)."""
    return sha256_bytes(getattr(json, '_a0_dumps', json.dumps)(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode())


def stub(capture):
    return capture.replace('/', '__')


def dataset(capture):
    """relift's two-way dataset split."""
    return 'ARKit' if capture.startswith('arkitscenes/') else 'ScanNet/ScanNet++'


def load_relift():
    """relift.py imported unchanged from its own path (module name 'relift')."""
    if 'relift' in sys.modules:
        return sys.modules['relift']
    spec = importlib.util.spec_from_file_location('relift', RELIFT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules['relift'] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- masks

def mask_sha(mask):
    """sha256 of a bool mask's C-order packbits plus its shape."""
    m = np.asarray(mask, bool)
    return sha256_bytes(getattr(json, '_a0_dumps', json.dumps)(list(m.shape)).encode()+np.packbits(m.reshape(-1)).tobytes())


def pack(masks):
    m = np.asarray(masks, bool)
    return dict(shape=list(m.shape), bits=base64.b64encode(np.packbits(m.reshape(-1)).tobytes()).decode())


def unpack(d):
    shape = tuple(d['shape']); n = int(np.prod(shape))
    return np.unpackbits(np.frombuffer(base64.b64decode(d['bits']), np.uint8), count=n).astype(bool).reshape(shape)


def seed_to_canvas(mask, resize):
    """GT/served 240x320 seed -> 480x640 tracker seed with the served raster's own resize
    (routed_features.resize: ndimage.zoom order 0, prefilter off), as K1's S_GT seeds were made."""
    return np.asarray(resize(np.asarray(mask, bool), CANVAS), bool)


def canvas_to_grid(mask480, resize=None):
    """Tracker video-resolution mask -> relift grid by the served path: resize to SHAPE (identity at 480x640), then [::2, ::2]
    (routed_features accepted candidates' masks[frame][::2, ::2])."""
    m = np.asarray(mask480, bool)
    if m.shape != CANVAS:
        if resize is None:
            raise ValueError('non-canvas tracker mask needs the served resize')
        m = np.asarray(resize(m, CANVAS), bool)
    return m[::2, ::2].copy()


def precision_recall(pred, truth):
    """Per-frame mask precision and recall over frames where GT or prediction is nonempty.
    precision_f = |P&G|/|P| on frames with P nonempty; recall_f = |P&G|/|G| on frames with G nonempty.
    Returns per-frame lists (None where undefined) for frames in the union, in frame order."""
    P = np.asarray(pred, bool).reshape(len(pred), -1); G = np.asarray(truth, bool).reshape(len(truth), -1)
    out = []
    for f in range(len(P)):
        p, g = int(P[f].sum()), int(G[f].sum())
        if not p and not g:
            continue
        inter = int((P[f] & G[f]).sum())
        out.append(dict(frame=f+1, precision=inter/p if p else None, recall=inter/g if g else None))
    return out


def summarize_pr(records):
    prec = [r['precision'] for r in records if r['precision'] is not None]
    rec = [r['recall'] for r in records if r['recall'] is not None]
    return dict(union_frames=len(records), pred_frames=len(prec), gt_frames=len(rec),
                precision=float(np.mean(prec)) if prec else None, recall=float(np.mean(rec)) if rec else None)


# ---------------------------------------------------------------- frames

def frame_manifests():
    f = json.loads(FRAMES_JSON.read_text()); d = json.loads(DENSE_JSON.read_text())
    caps = f['captures']; caps = {c['native']: c for c in caps} if isinstance(caps, list) else caps
    dense = d['captures']; dense = {c['native']: c for c in dense} if isinstance(dense, list) else dense
    return caps, dense


def binding(native, caps, dense):
    """frame_binding_sha256 exactly as h1eval/h10/parity_adapter.map_items computes it."""
    return digest(dict(anchors=caps[native], dense=dense[native]))


def resolve_frame(rel, sha):
    """(path, root) of the first store holding the content-addressed PNG; None when no store has it."""
    for root in FRAME_ROOTS:
        p = root/rel
        if p.is_file():
            return p, root
    return None, None


def read_frames_index():
    return json.loads(FRAMES_PATH.read_text())


# ---------------------------------------------------------------- population

def eligible(R, refs):
    """relift's eligible (item, operand) population in relift's own loop order (sorted GT captures, then manifest order),
    with its exclusions: GT capture missing, unbound operand, portrait GT orientation. No cell is computed."""
    expected = {r['capture'] for r in refs.values()}
    gt_paths = {}
    for folder in [R.BASE/'gt/t1_gt/gt', R.BASE/'gt/arkit_gt/gt']+R.NOGT_DIRS:
        for path in folder.glob('*.npz'):
            cap = path.stem.replace('__', '/') if '__' in path.stem else 'arkitscenes/'+path.stem
            if cap in expected:
                gt_paths[cap] = path
    if len(gt_paths) != R.EXPECTED_GT:
        raise ValueError('expected %d GT captures' % R.EXPECTED_GT)
    items, objects = [], []
    for cap, path in sorted(gt_paths.items()):
        with np.load(path, allow_pickle=False) as z:
            gt = {k: z[k] for k in ('inst', 'ids', 'labels', 'frame_indices', 'valid')}
        for iid, ref in refs.items():
            if ref['capture'] != cap:
                continue
            nn = R.names(ref)[0]
            bb = [R.bind(n, gt['ids'], gt['labels']) for n in nn]
            if any(b['instance_id'] is None for b in bb) or gt['inst'].shape[1:] != GRID:
                continue
            if gt['frame_indices'].tolist() != ref['source_indices'] or not gt['valid'].all():
                raise ValueError('GT anchor binding')
            items.append(dict(item_id=iid, capture=cap, gt_path=str(path)))
            for name, b in zip(nn, bb):
                objects.append(dict(item_id=iid, capture=cap, name=name, instance_id=int(b['instance_id'])))
    if len(items) != EXPECTED['items'] or len({i['capture'] for i in items}) != EXPECTED['captures']:
        raise ValueError('eligible population differs from relift: %d items, %d captures'
                         % (len(items), len({i['capture'] for i in items})))
    return items, objects, gt_paths


def depth_rows(R, depth=DEPTH, receipt=RECEIPT):
    """The dump's geometry rows by capture, read exactly as relift.run reads them."""
    rc = json.loads(Path(receipt).read_text())
    if not rc.get('verified', False):
        raise ValueError('depth upload not verified')
    reader = R.Records(depth, rc); out = {}
    for row in reader:
        cap = row['metadata']['capture']
        if cap in out:
            raise ValueError('duplicate depth capture')
        out[cap] = row
    if reader.report['salvaged']:
        raise ValueError('incomplete depth return')
    return out


# ---------------------------------------------------------------- io

def write_json(path, obj, gz=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    # relift installs an opaque-JSON transport that hex-wraps indented json.dumps; write plain JSON with the original.
    dumps = getattr(json, '_a0_dumps', json.dumps)
    text = dumps(obj, allow_nan=False, separators=(',', ':') if gz else None, indent=None if gz else 1)
    tmp = path.with_name(path.name+'.tmp')
    if gz:
        tmp.write_bytes(gzip.compress(text.encode(), 6))
    else:
        tmp.write_text(text+'\n')
    os.replace(tmp, path)
    return sha256_file(path)


def read_json(path):
    data = Path(path).read_bytes()
    return json.loads(gzip.decompress(data) if str(path).endswith('.gz') else data)


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
