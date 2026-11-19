"""CPU read trace of the delivered kit (sb_ktfix, read-only) under the GPU interpreter and PYTHONPATH.
Usage: trace_reads.py A|B|C. Records every path opened (and every directory listed) per phase, then
writes work/trace/trace_<part>.json. Never writes into the kit; never parses held-out labels."""
import sys, os, json, atexit, gc, time
PART = sys.argv[1]
KIT = '/scratch/jjyeung/orch_n30/sb_ktfix'
OUTF = f'/scratch/jjyeung/orch_n30/sb_ktrev2/work/trace/trace_{PART}.json'
PHASE = ['imports']
OPENS, LISTS, WRITES = {}, {}, []

def hook(event, args):
    if event == 'open':
        p = args[0]
        if isinstance(p, (str, bytes)):
            p = os.path.abspath(os.fsdecode(p)); mode, flags = args[1], args[2]
            w = (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)) or (isinstance(mode, str) and any(x in mode for x in 'wax+'))
            if w: WRITES.append((PHASE[0], p))
            else: OPENS.setdefault(p, PHASE[0])
    elif event in ('os.listdir', 'os.scandir', 'glob.glob'):
        p = args[0]
        if isinstance(p, (str, bytes)): LISTS.setdefault(os.path.abspath(os.fsdecode(p)), PHASE[0])
sys.addaudithook(hook)

def dump():
    os.makedirs(os.path.dirname(OUTF), exist_ok=True)
    with open(OUTF + '.tmp', 'w') as f:
        json.dump(dict(part=PART, opens=OPENS, lists=LISTS, writes=WRITES, done=PHASE[0]), f, indent=0, sort_keys=True)
    os.replace(OUTF + '.tmp', OUTF)
atexit.register(dump)

def phase(name):
    PHASE[0] = name; print(time.strftime('%H:%M:%S'), PART, name, flush=True)

sys.path.insert(0, KIT + '/code')
from common import *
import numpy as np
import runner
phase('preflight')
cfg = read_json(ROOT / 'configs/kit.json'); read_json(ROOT / 'out/DRYRUN.json'); digest(code_pins())
assert str(ROOT) == KIT

def g3t_load(c, n):
    from PIL import Image
    from student_pilot.tower_read import FrozenG3TTower
    m = manifest(); settings = m['gpu']
    frames = c['dense_frames'] if n == 64 else [c['dense_frames'][i] for i in c['anchor_slots']]
    for key in ('tower_weights', 'tower_config'):
        assert sha(settings[key]['path']) == settings[key]['sha256']
    for f in frames[:4]:
        assert sha(f['path']) == f['sha256']
        with Image.open(local(f['path'])) as im: im.convert('RGB')
    tower = FrozenG3TTower(dict(weights_path=settings['tower_weights']['path'], config_path=settings['tower_config']['path'], device='cpu', dense_frames=n, depth_chunk_size=8, dtype='bf16'))
    tower._load()
    from student_pilot.c1r_ref import source_import
    import student_pilot.tower_read as T
    from pathlib import Path as P
    source_import(P(T.__file__).parent / 'g3t_vendor')
    from vggt.utils.load_fn import load_and_preprocess_images_square
    from student_pilot._tower_native import selected_layers, native_sample
    del tower; gc.collect()

if PART in ('A', 'B'):
    phase('roster')
    from policy import captures
    roster = captures()
    train = [c for c in captures('train') if (capdir(c, '/scratch/jjyeung/k1/run_convert_2') / 'geometry.npz').is_file()][:2]
    held = captures('heldout')[:1]
    phase('binding')
    for c in train + held:
        runner.binding(c, PART)
        (capdir(c, '/scratch/jjyeung/k1/run_tower_sam_2') / 'tower.npz').exists()
    if PART == 'A':
        phase('g3t_load'); g3t_load(train[0], 32)
    else:
        phase('sam3_load_forward')
        import torch
        from PIL import Image
        from student_pilot.sam3_tower import Sam3Tower
        from student_pilot.routed_features import rle
        from e2e_reader.stage1 import sam3_detect
        c = train[0]; m = manifest()['gpu']
        for key in ('sam_checkpoint', 'sam_receipt'): assert sha(m[key]['path']) == m[key]['sha256']
        source = local(m['sam_source'])
        f = c['dense_frames'][1]; assert sha(f['path']) == f['sha256']
        with Image.open(local(f['path'])) as im: img = im.convert('RGB')
        tower = Sam3Tower(dict(device='cpu', checkpoint_path=m['sam_checkpoint']['path'], receipt_path=m['sam_receipt']['path'], source_root=str(source), precision='float32'))
        # Trace-only shim: upstream SAM 3 builders allocate with a literal device="cuda".
        saved = {n: getattr(torch, n) for n in ('zeros', 'ones', 'arange', 'empty', 'full', 'tensor', 'linspace', 'randn', 'rand')}
        def to_cpu(fn):
            def wrapped(*a, **k):
                if str(k.get('device', '')).startswith('cuda'): k['device'] = 'cpu'
                return fn(*a, **k)
            return wrapped
        for n, fn in saved.items(): setattr(torch, n, to_cpu(fn))
        _pin = torch.Tensor.pin_memory; torch.Tensor.pin_memory = lambda self, *a, **k: self
        try:
            tower._load()
            feats = tower.encode([img])
            name = sorted({n.strip().lower() for r in c['rows'] for n in r.get('operands', [])})[0]
            dets = sam3_detect(tower, feats, name)
        finally:
            for n, fn in saved.items(): setattr(torch, n, fn)
            torch.Tensor.pin_memory = _pin
        print('sam3 detections', len(dets), len(dets[0]), flush=True)
        del tower, feats; gc.collect()
    phase('cpu_pricing')
    import evaluate_v2 as E, metrics
    from replay import price, winning_box, flagged_row, selector_diagnostics
    from evaluate import geometry, stored_tower, scored, paired_scores
    lab = E.labels('train')
    for c in train:
        tw = stored_tower(c); gt = npz(c['gt']['path']); assert sha(c['gt']['path']) == c['gt']['sha256']
        own = npz(capdir(c, '/scratch/jjyeung/k1/own_170235/native/probe') / 'own.npz')
        cache = read_json(capdir(c, '/scratch/jjyeung/k1/run_convert_2') / 'candidates.json')
        geo, scale = geometry(tw, own)
        metrics.poses(metrics.c2w_pose(tw['raw_pose'][tw['anchor_slots']]), gt['c2w'], scale, gt['valid'])
        metrics.depth_metrics(tw['depth_grid'], gt['depth'], gt['valid'])
        today = scored(price(c, geo, cache=cache), 'C64_V32_today', lab)
        scored(price(c, geo, gt=gt), 'C64_V32_GTmask', lab)
        winning_box(dict(capture=c, cache=cache, geometry=geo, n_frames=32))
        if PART == 'A':
            E.scale_record(c, tw, own)
        else:
            [flagged_row(r, r) for r in price(c, geo, cache, 32)]
            selector_diagnostics(c, cache, geo, 32, gt)
            a_path = E.OUT / 'A_DISTANCE.txt'; a_path.exists()
    E.read_json(ROOT / 'configs/KBOX_WINNING_BOX_RULE.json')
    phase('heldout_look_inputs')
    # Same per-capture CPU inputs as train; labels are only located, never opened.
    for c in held:
        stored_tower(c); npz(c['gt']['path'])
        npz(capdir(c, '/scratch/jjyeung/k1/own_170235/native/probe') / 'own.npz')
        read_json(capdir(c, '/scratch/jjyeung/k1/run_convert_2') / 'candidates.json')
        g = capdir(c, '/scratch/jjyeung/k1/run_convert_2') / 'geometry.npz'
        if g.is_file(): npz(g)
else:
    phase('camera_items')
    from camera_records import records, frame_binding
    from camera_binding import camera_items
    records(); fb = frame_binding(); data = camera_items()
    print('frame_binding', fb['status'], fb['bound'], fb['bound64'], flush=True)
    phase('binding')
    cap = next(c for c in data['captures'] if c.get('has64'))
    runner.binding(cap, 'C', False); runner.binding(cap, 'C', True)
    phase('pricing_imports')
    import camera_pricing, camera
    import student_pilot.camera_targets, student_pilot.head_programs
    phase('da3_load_forward')
    sys.path.insert(0, '/scratch/jjyeung/geo_bakeoff_kit/work')
    from geo_bakeoff.backends import Backend
    backend = Backend('da3', device='cpu', threads=8, go_file=None)
    paths = [str(local(f['path'])) for f in cap['dense_frames']]
    from depth_anything_3.utils.io.input_processor import InputProcessor
    from geo_bakeoff.backends import read_rgb
    InputProcessor()([read_rgb(p) for p in paths], process_res=504, process_res_method='upper_bound_resize', num_workers=1, sequential=True)
    p = backend.predict(paths[:2])
    print('da3', p.depth.shape, flush=True)
    del backend; gc.collect()
phase('done')
