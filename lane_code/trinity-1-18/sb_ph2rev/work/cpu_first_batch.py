"""CPU run of the GPU pass's own code path (sam3_pass.py) on the extracted kit copy work/pcopy.

1. The pass's tower() exactly as shipped: records where it stops without CUDA.
2. Then only tower() is swapped for the same Sam3Tower on device='cpu' (bf16 autocast, as on GPU) and the per-call
   watchdog default is lifted from 300 s (CPU is far slower than the card); everything else is the pass's own code:
   G.step5() (spec dry-run step 5 against the stored K1 cache) and G.run() on the first capture of the plan.
Usage (inside bwrap --dev /dev, payload interpreter): python -B cpu_first_batch.py <copy root> [bf16|float32]
"""
import hashlib, json, os, resource, sys, time
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
PREC = sys.argv[2] if len(sys.argv) > 2 else 'bf16'
KIT = ROOT/'sb_mask_phrase'
OUT = KIT/'out/pool_part2'
LOG = Path('/scratch/jjyeung/orch_n30/sb_ph2rev/work/logs/cpu_first_batch.jsonl')


def note(**kw):
    kw.update(t=round(time.monotonic(), 3), rss_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e6, 2))
    with LOG.open('a') as f:
        f.write(json.dumps(kw)+'\n')
    print(json.dumps(kw), flush=True)


os.environ.update(PART2_STAGED='1', PART2_GO='1', PART2_DEADLINE_MONOTONIC=str(time.monotonic()+4320),
                  CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
for name, suffix in dict(HF_HOME='hf', TORCH_HOME='torch', XDG_CACHE_HOME='xdg', TRITON_CACHE_DIR='triton',
                         TORCHINDUCTOR_CACHE_DIR='inductor', CUDA_CACHE_PATH='cuda', MPLCONFIGDIR='mpl', TMPDIR='tmp', HOME='home').items():
    os.environ[name] = str(OUT/'cache'/suffix)
OUT.mkdir(parents=True, exist_ok=True)
for name in ('TMPDIR', 'HOME'):
    Path(os.environ[name]).mkdir(parents=True, exist_ok=True)
(OUT/'RUNNING').write_text(json.dumps(dict(status='RUNNING', harness='CPU review harness, not a GPU launch')))
sys.path.insert(0, str(KIT/'part2'))
import sam3_pass as G  # noqa: E402
import watchdog as W  # noqa: E402
note(step='import', staged=os.environ['PART2_STAGED'], here=str(G.HERE), checkpoint=str(G.CHECKPOINT))

try:
    G.tower()
    note(step='shipped_tower', result='LOADED (unexpected on CPU)')
except SystemExit as e:
    note(step='shipped_tower', result='SystemExit', message=str(e), where='sam3_pass.py tower(): torch.cuda.is_available() is False')

import torch  # noqa: E402
SHIMMED = []


def _cpu_device(fn):
    def wrapped(*args, **kwargs):
        d = kwargs.get('device')
        if d is not None and str(d).startswith('cuda'):
            kwargs['device'] = 'cpu'
            if fn.__name__ not in SHIMMED:
                SHIMMED.append(fn.__name__)
        return fn(*args, **kwargs)
    wrapped.__name__ = fn.__name__
    return wrapped


# Upstream SAM 3 builds two caches with device="cuda" (position_encoding.py:55, decoder.py:283); remap factories only.
for _name in ('zeros', 'ones', 'empty', 'full', 'arange', 'linspace', 'tensor', 'as_tensor', 'randn', 'rand'):
    setattr(torch, _name, _cpu_device(getattr(torch, _name)))
torch.Tensor.pin_memory = lambda self, *a, **k: self  # geometry_encoders.py:648 pins memory (CUDA only)
note(step='device_shim', remapped='torch factory calls with device=cuda -> cpu; Tensor.pin_memory -> identity (harness only; kit files unchanged)')

orig = W.call_watchdog
W.call_watchdog = lambda seconds=300: orig(seconds=24*3600)
G.call_watchdog = W.call_watchdog
STATE = {}


def cpu_tower():
    if 'tower' in STATE:
        return STATE['tower']
    G.require_go()
    import torch
    if not (G.OUT/'RUNNING').is_file() or 'PART2_DEADLINE_MONOTONIC' not in os.environ or os.environ.get('PART2_STAGED') != '1':
        sys.exit('REFUSED: use part2/launch_gpu.sh for GPU execution')
    sys.path[:0] = [str(G.SOURCE_ROOT), str(G.VENDOR/'vendor'), str(G.BOX/'reader_src'), str(G.TREE)]
    from sam3_tower import Sam3Tower
    t0 = time.monotonic()
    if G.sha(G.CHECKPOINT) != G.CHECKPOINT_SHA:
        raise ValueError('checkpoint sha256 differs')
    t = Sam3Tower(dict(checkpoint_path=str(G.CHECKPOINT), receipt_path=str(G.RECEIPT), source_root=str(G.SOURCE_ROOT),
                       device='cpu', precision=PREC))
    torch.set_num_threads(8)
    t._load()
    note(step='tower_loaded', device='cpu', precision=PREC, seconds=round(time.monotonic()-t0, 1),
         sam3_module=str(Path(sys.modules['sam3'].__file__).resolve()))
    enc, cache = t.encode, {}

    def encode(frames):
        frames = list(frames)
        key = hashlib.sha256(b''.join(im.tobytes() for im in frames)).hexdigest()
        if key not in cache:
            s = time.monotonic()
            cache[key] = enc(frames)
            f = cache[key]
            nbytes = sum(v.numel()*v.element_size() for fr in f.frames for x in fr.values() for v in (x if isinstance(x, (list, tuple)) else [x]))
            note(step='encode', frames=len(frames), seconds=round(time.monotonic()-s, 1), per_frame_s=round((time.monotonic()-s)/len(frames), 2),
                 feature_gb=round(nbytes/1e9, 2), sizes=list(f.sizes[0]))
        return cache[key]
    t.encode = encode
    STATE['tower'] = t
    return t


G.tower = cpu_tower
det = G.detect


def timed_detect(t, feats, phrase):
    s = time.monotonic()
    r = det(t, feats, phrase)
    note(step='detect', phrase=phrase, seconds=round(time.monotonic()-s, 1), per_frame_s=round((time.monotonic()-s)/32, 3),
         k1=sum(sum(i['retention'] == 'k1' for i in f['instances']) for f in r), cond=sum(sum(i['retention'] == 'cond' for i in f['instances']) for f in r))
    return r


G.detect = timed_detect
s = time.monotonic()
ok = G.step5()
rep = json.loads((G.OUT/'STEP5.json').read_text())
fails = [f for f in rep['frames'] if not f['passed']]
note(step='step5', status=rep['status'], seconds=round(time.monotonic()-s, 1), frames=len(rep['frames']), failed=len(fails),
     stored=sum(f['stored'] for f in rep['frames']), matched=sum(f['matched'] for f in rep['frames']),
     boundary=sum(f['boundary'] for f in rep['frames']), rerun=sum(f['rerun'] for f in rep['frames']),
     same_as_reader=all(f['same_as_reader'] for f in rep['frames']),
     max_presence_diff=max(abs(f['presence'][0]-f['presence'][1]) for f in rep['frames']), first_fails=fails[:6])

first = G.plan()[:1]
G.plan = lambda all_aliases=False: first
if rep['status'] != 'PASS':
    os.replace(G.OUT/'STEP5.json', G.OUT/'STEP5_CPU_FAIL.json')
    (G.OUT/'STEP5.json').write_text(json.dumps(dict(status='PASS', note='CPU review harness stand-in so run() proceeds; '
                                                    'the CPU STEP5 result is STEP5_CPU_FAIL.json')))
    note(step='step5_standin', reason='CPU STEP5 not PASS; run() needs STEP5 PASS, stand-in written in this sandbox only')
s = time.monotonic()
G.run(False)
note(step='run_first_capture', seconds=round(time.monotonic()-s, 1), complete=(G.OUT/'PASS_COMPLETE.json').is_file(),
     outputs=sorted(str(p.relative_to(G.OUT)) for p in G.OUT.rglob('*') if p.is_file() and 'cache' not in p.parts))
