"""Shared paths, population, frame binding and mask codecs for the J1 kit (lane lever8, trinity-2-28; ORCH RULING
2026-11-22T04:38Z). Copy of lever7/gtcd/kit/gtc_common.py with the dense and seed parts removed and J1's paths added.
J1 runs SAM 3's frozen image detector on the 32 served anchors of relift's 46 captures: text prompts per operand name (arms
h1, h0) and the bound GT instance's tight box as a box prompt (arm k). relift.py is imported from its own path, unchanged.
Read-only inputs: lever6/gtc/out/FRAMES_GTC.json (anchor index and pinned sha256 per slot), lever7/gtcd/arkit/frames_k6
(ARKit anchors, OpenCV 4.14.0 decode), the served sources (byte-identical copies under j1/served, pinned below).
numpy/stdlib only at import time, so the SAM 3 interpreter can import this module too.
"""
import base64, gzip, hashlib, importlib.util, json, os, sys, time
from pathlib import Path
import numpy as np

KIT = Path(__file__).resolve().parent
ROOT = KIT.parent                                      # /scratch/jjyeung/orch_n30/lever8/j1
OUT = ROOT/'out'
DETECT = OUT/'detect'                                  # GPU job output: <capture stub>.json.gz per capture
FRAMES_DIR = ROOT/'frames'                             # kit-local anchor copies: <capture stub>/<slot>.png (sha-checked)
FRAMES_J1 = OUT/'FRAMES_J1.json'
PROMPTS_J1 = OUT/'PROMPTS_J1.json'
SERVED = ROOT/'served'                                 # byte-identical copies of the served grounding sources
PYEXTRA = ROOT/'pyextra'                               # scipy 1.14.1 (p1cpu copy); the SAM 3 env has none, routed_features needs it
GTC_OUT = Path('/scratch/jjyeung/orch_n30/lever6/gtc/out')
FRAMES_PATH = GTC_OUT/'FRAMES_GTC.json'
ARKIT_FRAMES = Path('/scratch/jjyeung/orch_n30/lever7/gtcd/arkit/frames_k6')   # <id>/<native index %06d>.png
ARKIT_DECODE = Path('/scratch/jjyeung/orch_n30/lever7/gtcd/arkit/DECODE_ARKIT_K6.json')
RELIFT = Path('/scratch/jjyeung/orch_n30/lever5/r1x/r1/relift.py')
DEPTH = Path('/scratch/jjyeung/orch_n30/lever1_c/r1/returned/0.gz')
RECEIPT = Path('/scratch/jjyeung/orch_n30/lever1_c/r1/returned/4.json')  # the 0.gz object receipt (sha256, verified), as lever6/lever7 pass it
ITEMS = Path('/scratch/jjyeung/orch_n30/grd_funnel1/kit/rerun2/items544.json')
META = Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/work/meta/x')
FRAMES_JSON = META/'sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json'
DENSE_JSON = META/'sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json'
SAM3_SOURCE = Path('/scratch/jjyeung/b01ec87a6f29b/d/s')
SAM3_CHECKPOINT = Path('/scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt')
SAM3_RECEIPT = Path('/scratch/jjyeung/b01ec87a6f29b/d/k/SAM3_RECEIPT.json')
# sha256 of the served grounding sources in the read package of Orchard job 174135 (lever1_c/r1/out/IMPORT_AUDIT.json),
# equal to cont_ops24_c/gbuild/work/payload; detect.py imports the j1/served copies only after checking these.
SERVED_PINS = {
    'b/e2e_reader/__init__.py': '481d2c8a8b5e38f7a39cc38635a64d97672e8fa1b4520e2c8aa4d13300b9106c',
    'b/e2e_reader/stage1.py': 'b1a77424a2a014b12890805d8c72f1a83dd5e378cd54a2ff221887ccde1cafe1',
    'tree/student_pilot/__init__.py': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'tree/student_pilot/routed_features.py': '736c5a642fe28656c5508022210b050a87e49821381980a9c6f79007ef1fda13',
    'tree/student_pilot/routed_candidates.py': '9a2004108d85f3c2a70ca5e4d66240748807d4f0c3ced8a2e0842fea4d78482f',
    'tree/student_pilot/sam3_tower.py': '617d5c8daa31ee2de62efe5c93ed32f50203805006dce5bb75d9959a16e4decb'}
CANVAS = (480, 640)   # served SHAPE (routed_features.py:8); every proposal mask is stored at this size
GRID = (240, 320)     # relift's (32,240,320) cell grid = CANVAS[::2, ::2] (routed_features.py:199)
EXPECTED = dict(items=117, captures=46)
FINE = dict(scannet='ScanNet', scannetppv2='ScanNet++', scannetpp='ScanNet++', arkitscenes='ARKit')
DATASETS3 = ('ARKit', 'ScanNet', 'ScanNet++')


def fine(capture):
    """Three-way dataset of a capture (ARKit, ScanNet, ScanNet++)."""
    return FINE[capture.split('/', 1)[0]]


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
    empty_gt = sum(1 for r in records if r['recall'] is None)   # anchors where the arm has a mask and GT is empty
    return dict(union_frames=len(records), pred_frames=len(prec), gt_frames=len(rec), pred_on_empty_gt=empty_gt,
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

def _scalar(x):
    if hasattr(x, 'item'):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    raise TypeError('not JSON serialisable: %r' % type(x))


def dumps_plain(obj):
    """One-line plain JSON (relift's opaque transport bypassed), numpy scalars converted, NaN refused."""
    return getattr(json, '_a0_dumps', json.dumps)(obj, allow_nan=False, default=_scalar)


def write_json(path, obj, gz=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    # relift installs an opaque-JSON transport that hex-wraps indented json.dumps; write plain JSON with the original.
    dumps = getattr(json, '_a0_dumps', json.dumps)
    text = dumps(obj, allow_nan=False, default=_scalar, separators=(',', ':') if gz else None, indent=None if gz else 1)
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
