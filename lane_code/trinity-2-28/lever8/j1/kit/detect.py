"""J1 step 3 (GPU job, one card on trinity-0-13 at normal priority): SAM 3's frozen image detector on the 32 served anchors of
relift's 46 captures, through the served grounding code, plus GT box prompts for arm k. Writes every retained proposal, so
h1 and h0 are chosen on CPU afterwards (relift_j1.py).

Served path, imported unchanged from byte-identical copies under j1/served (sha256 pinned in j1_common.SERVED_PINS, equal to
the read package of Orchard job 174135):
  tower    student_pilot.sam3_tower.Sam3Tower(checkpoint, receipt, source root, device): pinned checkpoint and sources checked on
           load (sam3_tower.py:149-182); bf16 autocast on CUDA, float32 on CPU (sam3_tower.py:126, 184-193).
  frames   PIL RGB from the anchor PNG bytes (h1eval/native.py:94), sha256 checked against FRAMES_J1 before decoding.
  encode   Sam3Tower.encode once per capture (sam3_tower.py:195-221).
  text     e2e_reader.stage1.sam3_detect(tower, features, name) per operand name (stage1.py:76-106): phrase strip+lower, retention
           score x presence >= 0.05 in score order, cap 30, masks bilinear to the frame size > 0 then resized to 480x640.
Arm k (oracle, no served function exists): the GT instance's tight box as the only prompt, run on the same stored features as
  Sam3Processor.add_geometric_prompt runs it (sam3/model/sam3_image_processor.py:128-152: text 'visual', the dummy prompt plus
  one positive box, normalised cx, cy, w, h) and scored as its _forward_grounding scores (lines 183-196: sigmoid(logit) x
  presence); the top-scoring query's mask goes through stage1's mask rule (bilinear to the frame size, > 0, resize to 480x640).
Outputs under --out (on /scratch): <capture stub>.json.gz per capture (packed 480x640 masks plus scores, per-capture timing and
peak memory), EVENTS.jsonl, INDEX.json. Finished capture files are the partial result: a resume skips files of the same contract
and refuses others; a signal writes KILLED, and a killed directory is not resumed. A capture whose anchor bytes differ from
FRAMES_J1 fails (status SHA_MISMATCH in INDEX.json); nothing is substituted.
Usage (SAM 3 interpreter /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python; launch_gpu.sh writes the line):
  python detect.py --device cuda --out ../out/detect --captures all
  python detect.py --device cpu --out ../work/rehearsal_cpu --captures scannet/scene0642_01      (CPU rehearsal)
  python detect.py --forecast                                                                    (no torch)
"""
import argparse, io, json, os, resource, signal, sys, time
from pathlib import Path
import numpy as np
KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))
import j1_common as G
import select_j1 as S

CODE = ('detect.py', 'j1_common.py', 'select_j1.py')
# Rates: SAM 3 image embed 0.080 s/frame (K1 TIMING_RECEIPT, RTX 6000 Ada), 0.064 s per prompt-frame (K1 teacher pass), load 9 s.
RATES = dict(embed_per_frame=0.080, prompt_per_frame=0.064, box_per_frame=0.064, load_seconds=9., per_capture_overhead=2.)
STATE = dict(events=None)


def event(kind, **kw):
    rec = dict(time=G.utc(), event=kind, host=os.uname().nodename, pid=os.getpid(), **kw)
    line = json.dumps(rec, default=str)
    if STATE['events']:
        with open(STATE['events'], 'a') as f:
            f.write(line+'\n')
    print(line, flush=True)


def forecast(prompts, captures):
    caps = [c for c in prompts['captures'] if captures == 'all' or c['capture'] in captures]
    rows = [dict(capture=c['capture'], seconds=RATES['per_capture_overhead']+32*RATES['embed_per_frame']
                 + c['text_prompt_frames']*RATES['prompt_per_frame']+c['box_prompt_frames']*RATES['box_per_frame']) for c in caps]
    return dict(total_seconds=RATES['load_seconds']+sum(r['seconds'] for r in rows), captures=len(rows), rates=RATES,
                frames=32*len(rows), text_prompt_frames=sum(c['text_prompt_frames'] for c in caps),
                box_prompt_frames=sum(c['box_prompt_frames'] for c in caps), rows=rows)


def served_modules():
    """Check the served copies against their pins, then import them unchanged (scipy from j1/pyextra, after the env)."""
    for rel, pin in G.SERVED_PINS.items():
        if G.sha256_file(G.SERVED/rel) != pin:
            raise SystemExit('served source differs from its 174135 pin: '+rel)
    for name in ('e2e_reader', 'student_pilot', 'scipy'):
        if name in sys.modules:
            raise SystemExit('module imported before the served copies: '+name)
    sys.path[:0] = [str(G.SERVED/'b'), str(G.SERVED/'tree')]
    sys.path.append(str(G.PYEXTRA))
    from e2e_reader import stage1 as S1
    from student_pilot import sam3_tower as T
    from student_pilot import routed_features as F
    import scipy
    for m in (S1, T, F):
        if not str(Path(m.__file__).resolve()).startswith(str(G.SERVED.resolve())):
            raise SystemExit('served module loaded from outside j1/served: '+m.__file__)
    return S1, T, F, dict(scipy=scipy.__version__, scipy_file=scipy.__file__)


def contract(args, frames_sha, prompts_sha, versions):
    code = {n: G.sha256_file(KIT/n) for n in CODE}
    code.update({'served/'+k: v for k, v in G.SERVED_PINS.items()})
    return dict(schema='j1-detect-v1', code=code, frames_j1_sha256=frames_sha, prompts_j1_sha256=prompts_sha, device=args.device,
                anchor_limit=args.anchor_limit, receipt_sha256=G.sha256_file(G.SAM3_RECEIPT), retention=dict(joint_floor=S.JOINT_FLOOR, cap=S.CAP),
                mask_shape=list(G.CANVAS), versions=versions)


def load_images(frames, limit):
    """PIL RGB anchors after a byte sha256 check; raises ValueError('SHA_MISMATCH ...') on any difference."""
    from PIL import Image
    out = []
    for f in frames[:limit]:
        b = (G.ROOT/f['file']).read_bytes()
        if G.sha256_bytes(b) != f['sha256']:
            raise ValueError('SHA_MISMATCH slot %d' % f['slot'])
        with Image.open(io.BytesIO(b)) as im:
            out.append(im.convert('RGB'))
    return out


def cpu_redirect():
    """CPU rehearsal only (source untouched): SAM 3's source creates some tensors with a literal device='cuda'
    (sam3/model/position_encoding.py:55); map literal CUDA devices to the CPU, as K1's kit does
    (sb_cachk/kit_v2/mc_tracker.py:71-84, copied). Sam3Tower's float32 autocast already replaces the bf16 MLP cast."""
    import torch
    from torch.overrides import TorchFunctionMode

    class CpuRedirect(TorchFunctionMode):
        def __torch_function__(self, func, types, args=(), kwargs=None):
            kwargs = dict(kwargs or {})
            if func is torch.Tensor.cuda or func is torch.Tensor.pin_memory:
                return args[0]
            if str(kwargs.get('device', '')).startswith('cuda'):
                kwargs['device'] = 'cpu'
            if kwargs.get('pin_memory'):
                kwargs['pin_memory'] = False
            if func is torch.Tensor.to and args[1:] and str(args[1]).startswith('cuda'):
                args = (args[0], 'cpu') + tuple(args[2:])
            return func(*args, **kwargs)
    mode = CpuRedirect(); mode.__enter__()
    return 'TorchFunctionMode CpuRedirect: device cuda -> cpu, Tensor.cuda and Tensor.pin_memory -> identity, Tensor.to(cuda) -> cpu'


def box_detect(tower, features, f, box, visual, F):
    """Arm k on stored frame f: Sam3Processor.add_geometric_prompt's forward on the tower's features; the top query by
    sigmoid(logit) x presence; its mask by stage1's rule. Returns a record with the packed 480x640 mask."""
    import torch
    import torch.nn.functional as TF
    model = tower._backend.model; dev = tower.device
    stored, (h, w) = features.frames[f], features.sizes[f]
    backbone = {k: (v.to(dev) if hasattr(v, 'to') else [x.to(dev) for x in v]) for k, v in stored.items()}
    backbone['vision_features'] = backbone['backbone_fpn'][-1]
    backbone.update(visual)
    prompt = model._get_dummy_prompt()
    prompt.append_boxes(torch.tensor(box, device=dev, dtype=torch.float32).view(1, 1, 4),
                        torch.tensor([True], device=dev, dtype=torch.bool).view(1, 1))
    with torch.inference_mode(), tower._autocast():
        raw = model.forward_grounding(backbone_out=backbone, find_input=tower._backend.find_stage, geometric_prompt=prompt,
                                      find_target=None)
    cond = raw['pred_logits'].sigmoid().reshape(-1).float()
    presence = float(raw['presence_logit_dec'].sigmoid().item())
    prob = cond*presence
    order = torch.argsort(prob, descending=True, stable=True)
    i = int(order[0])
    native = raw['pred_masks'].reshape(-1, *raw['pred_masks'].shape[-2:])
    m = (TF.interpolate(native[i][None, None].float(), (h, w), mode='bilinear', align_corners=False)[0, 0] > 0)
    mask = F.resize(m.cpu().numpy(), F.SHAPE)
    vals = [float(prob[i]), float(cond[i]), presence]
    if not np.isfinite(vals).all():
        raise ValueError('nonfinite box score')
    return dict(slot=f+1, box=box, score=vals[0], cond_score=vals[1], presence=vals[2], query=i,
                queries_above_half=int((prob > .5).sum()), mask_pixels=int(mask.sum()), mask=G.pack(mask))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--device', choices=['cuda', 'cpu'])
    ap.add_argument('--out', default=str(G.DETECT))
    ap.add_argument('--captures', default='all')
    ap.add_argument('--anchor-limit', type=int, default=32)
    ap.add_argument('--hard-stop', type=float, default=3300.)
    ap.add_argument('--rss-limit-gib', type=float, default=60.)
    ap.add_argument('--threads', type=int, default=8)
    ap.add_argument('--forecast', action='store_true')
    args = ap.parse_args(argv)
    prompts = G.read_json(G.PROMPTS_J1); frames = {c['capture']: c for c in G.read_json(G.FRAMES_J1)['captures']}
    if prompts['frames_j1_sha256'] != G.sha256_file(G.FRAMES_J1):
        raise SystemExit('PROMPTS_J1 was built on another FRAMES_J1')
    captures = 'all' if args.captures == 'all' else set(args.captures.split(','))
    if captures != 'all' and captures - set(frames):
        raise SystemExit('--captures names captures outside the eligible population')
    if not 1 <= args.anchor_limit <= 32:
        raise SystemExit('--anchor-limit takes 1..32')
    if args.forecast:
        f = forecast(prompts, captures); f.pop('rows'); print(json.dumps(f, indent=1)); return 0
    if args.device is None:
        raise SystemExit('--device required')
    out = Path(args.out).resolve()
    if not str(out).startswith('/scratch/') or not str(Path.cwd().resolve()).startswith('/scratch/'):
        raise SystemExit('runs from /scratch and writes to /scratch only')
    out.mkdir(parents=True, exist_ok=True)
    STATE['events'] = out/'EVENTS.jsonl'
    if (out/'KILLED').exists():
        event('REFUSED', reason='a previous pass in this directory was killed; it is reported, not resumed'); return 3
    S1, T, F, versions = served_modules()
    spec = contract(args, G.sha256_file(G.FRAMES_J1), G.sha256_file(G.PROMPTS_J1), versions)
    t0 = time.monotonic()

    def on_term(signum, frame):
        (out/'KILLED').write_text(f'{G.utc()} signal {signum}\n')
        event('KILLED', signal=signum, seconds=time.monotonic()-t0, note='finished capture files are the partial result')
        os._exit(128+signum)
    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(sig, on_term)
    work = [c for c in prompts['captures'] if captures == 'all' or c['capture'] in captures]
    fc = forecast(prompts, captures)
    event('START', device=args.device, captures=len(work), anchor_limit=args.anchor_limit, cuda_visible=os.environ.get('CUDA_VISIBLE_DEVICES'),
          contract=spec, forecast_seconds=fc['total_seconds'])
    try:
        return run(args, out, spec, frames, work, t0, S1, T, F)
    except BaseException as e:
        event('FAILED', error=repr(e)[:800], seconds=time.monotonic()-t0)
        raise


def run(args, out, spec, frames, work, t0, S1, T, F):
    import torch
    torch.set_num_threads(args.threads)
    if args.device == 'cuda':
        if not torch.cuda.is_available():
            raise SystemExit('no CUDA device visible')
        if torch.cuda.get_device_capability(0) < (8, 0):
            event('REFUSED', reason='card without native bf16'); return 6
    shims = []
    if args.device == 'cpu':
        if torch.cuda.is_available():
            raise SystemExit('CPU run sees a CUDA device; set CUDA_VISIBLE_DEVICES to empty')
        shims.append(cpu_redirect())
    l0 = time.monotonic()
    tower = T.Sam3Tower(dict(checkpoint_path=str(G.SAM3_CHECKPOINT), receipt_path=str(G.SAM3_RECEIPT),
                             source_root=str(G.SAM3_SOURCE), device=args.device))
    tower._load()
    with torch.inference_mode(), tower._autocast():
        visual = tower._backend.model.backbone.forward_text(['visual'], device=str(tower.device))
    load_s = time.monotonic()-l0
    import psutil
    proc = psutil.Process()
    event('LOADED', load_seconds=load_s, precision=tower.precision, device=torch.cuda.get_device_name(0) if args.device == 'cuda' else 'cpu',
          card_bytes=torch.cuda.get_device_properties(0).total_memory if args.device == 'cuda' else None,
          sam3_module=sys.modules['sam3'].__file__, shims=shims)
    done, failed, stopped, peak = 0, [], None, 0.
    for c in work:
        cap = c['capture']; path = out/(G.stub(cap)+'.json.gz')
        if path.exists():
            if G.read_json(path).get('contract') != spec:
                raise SystemExit(f'{path} was written under another contract; move it aside (incompatible resume)')
            done += 1; continue
        if time.monotonic()-t0 > args.hard_stop:
            stopped = f'HARD_STOP before {cap}'; break
        u0 = time.monotonic()
        if args.device == 'cuda':
            torch.cuda.reset_peak_memory_stats()
        try:
            images = load_images(frames[cap]['frames'], args.anchor_limit)
        except ValueError as e:
            failed.append(dict(capture=cap, status=str(e))); event('CAPTURE_FAILED', capture=cap, reason=str(e)); continue
        png_s = time.monotonic()-u0
        e0 = time.monotonic(); features = tower.encode(images); encode_s = time.monotonic()-e0
        n = len(images); text = {}; kept = 0
        x0 = time.monotonic()
        for p in c['prompts']:
            raw = S1.sam3_detect(tower, features, p)
            if len(raw) != n:
                raise RuntimeError('sam3_detect frame count')
            rec = []
            for fr in raw:
                vals = [(e['score'], e['presence']) for e in fr]
                if not np.isfinite(np.asarray(vals, float)).all():
                    raise ValueError('nonfinite proposal score')
                rec.append([dict(score=float(e['score']), presence=float(e['presence']), mask=G.pack(e['mask'])) for e in fr])
                kept += len(fr)
            text[p] = rec
        text_s = time.monotonic()-x0
        b0 = time.monotonic(); k = {}
        for u in c['k_units']:
            k[str(u['instance_id'])] = dict(instance_id=u['instance_id'], gt_sha256=u['gt_sha256'],
                                            anchors=[box_detect(tower, features, b['slot']-1, b['box'], visual, F)
                                                     for b in u['boxes'] if b['slot'] <= n])
        box_s = time.monotonic()-b0
        del features
        gib = torch.cuda.max_memory_allocated()/2**30 if args.device == 'cuda' else None
        rgib = torch.cuda.max_memory_reserved()/2**30 if args.device == 'cuda' else None
        if args.device == 'cuda':
            torch.cuda.empty_cache()
        peak = max(peak, rgib or 0.)
        sec = time.monotonic()-u0
        boxes = sum(len(v['anchors']) for v in k.values())
        G.write_json(path, dict(contract=spec, capture=cap, anchors=n, frames=[dict(slot=f['slot'], sha256=f['sha256']) for f in frames[cap]['frames'][:n]],
                                text=text, k=k, proposals=kept, box_prompts=boxes, png_seconds=png_s, encode_seconds=encode_s,
                                text_seconds=text_s, box_seconds=box_s, seconds=sec, cuda_peak_alloc_gib=gib, cuda_peak_reserved_gib=rgib,
                                rss_gib=proc.memory_info().rss/2**30, peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20), gz=True)
        done += 1
        event('CAPTURE', capture=cap, anchors=n, prompts=len(c['prompts']), proposals=kept, box_prompts=boxes,
              encode_seconds=encode_s, text_seconds=text_s, box_seconds=box_s, seconds=sec, cuda_peak_alloc_gib=gib,
              cuda_peak_reserved_gib=rgib, peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20, elapsed=time.monotonic()-t0)
        if proc.memory_info().rss > args.rss_limit_gib*2**30:
            stopped = f'RSS above {args.rss_limit_gib} GiB after {cap}'; break
    G.write_json(out/'INDEX.json', dict(done=done, captures=len(work), failed=failed, stopped=stopped, contract=spec,
                                        seconds=time.monotonic()-t0, load_seconds=load_s,
                                        cuda_peak_reserved_gib=peak if args.device == 'cuda' else None))
    event('END', done=done, captures=len(work), failed=failed, stopped=stopped, seconds=time.monotonic()-t0)
    return 0 if not stopped and not failed else 2


if __name__ == '__main__':
    sys.exit(main())
