"""GTC-D step 2 (GPU job, one 49 GB card; trinity-0-13 at normal priority): SAM 3 video tracker, arm d only, over each eligible
ScanNet/ScanNet++ capture's dense frame sequence (dense/DENSE_D.json), read out at the 32 served anchors.
Copy of the GTC-B kit's track.py with arm d in place of b; a, e, t, s and b are not run here.

Seeds: b's seeds (lever6/gtcb SEEDS_GTCB.json and seeds/*.npz; the GT instance on its largest anchor), used from the kit's
copies in out/seeds_b, which must be bit-identical to the gtcb originals (checked at start against SEEDS_GTCB.json's
seeds_sha256, the sha256 of the lever6 original file when present, and lever6/gtcb/SHA256SUMS_GTCB). Arm d keeps b's unit ids.
Each seed is placed on its anchor's position in the dense sequence (every anchor is a dense frame).
Frames: dense/DENSE_D.json (dense.py; captures with status OK only; others are listed as skipped, not substituted). Every frame's
PNG is verified against its manifest sha256 on read, and every anchor's sha256 must equal FRAMES_GTC.
Tracker: sb_cachk/kit_v2/mc_tracker.Sam3Carry, imported unchanged (pinned checkpoint and sources verified on load). A unit is one
capture: its dense frames are embedded once (K1's Sam3Carry.embed on chunks of 32 frames, the same per-frame features), and every
seed of the capture is carried over that shared cache one at a time, forward then backward over the whole dense sequence.
Memory: the cached normalised image is kept in host memory (it is unused by the tracker's SimpleMaskEncoder memory path; the
pass refuses another memory encoder), and the position encoding is shared after an equality check across chunks.
Carry rule (K1 mc_track_io.object_record), at the 32 anchors only: the seed anchor keeps the seed mask itself; another anchor
carries when the tracker's object score is positive, with no other threshold; otherwise it is empty.
Masks: 480x640 tracker masks reach relift's 240x320 grid by the served path (identity resize, then [::2, ::2]).
Outputs (under --out on /scratch): d/<capture>.json.gz per capture (packed (32,240,320) masks, anchor scores, dense frame count,
wall time, peak GPU memory), EVENTS.jsonl, INDEX.json. Finished capture files are the partial result; a resume skips files that
bind the same contract and refuses one that does not; a pass killed by a signal records KILLED and is not resumed without an order.
ARKit unit (kit_ark): the same pass on the ARKit manifest, --dense ../dense_ark/DENSE_D_ARK.json --out ../out_ark/track (or env
GTCD_DENSE, GTCD_TRACK_OUT; arguments win). Defaults are the ScanNet unit's dense/DENSE_D.json and out/track. A non-default
manifest writing into out/track, or the ScanNet manifest writing into out_ark/track, is refused.
Usage (SAM 3 interpreter /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python):
  python track.py --device cuda [--arms d] [--out ../out/track] [--dense ../dense/DENSE_D.json]
  python track.py --forecast                      (no torch; GPU-second forecast from K1's rates)
  python track.py --device cpu --captures scannet/scene0380_01 --out <dir>      (CPU rehearsal; launch_gpu.sh rehearse-cpu)
"""
import argparse, json, os, resource, signal, sys, time
from pathlib import Path
import numpy as np
KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))
import gtc_common as G

# K1 measured rates (sb_cachk/out/v2/track/TIMING_RECEIPT.json, RTX 6000 Ada, 2026-11-19)
K1 = dict(embed_per_frame=0.08010633658593776, track_per_object_frame=0.01005735398660766,
          overhead_per_unit=0.42716512249990046, load_seconds=8.881444379999948, peak_alloc_gib_64frames=5.288, peak_reserved_gib_64frames=5.559)
# GPU bytes per cached dense frame (bf16 backbone_fpn after conv_s0/conv_s1: 32x288x288 + 64x144x144 + 256x72x72) and the
# tracker's per-frame stored state (bf16 maskmem 64x72x72, fp32 pred_masks 288x288, obj_ptr); base = K1's 64-frame peak minus
# its 64 cached frames (which also held the fp32 1008x1008 image on the card).
FRAME_BYTES = 2*(32*288*288+64*144*144+256*72*72)
STATE_BYTES = 2*64*72*72+4*288*288+4*256
IMAGE_BYTES = 4*3*1008*1008
CODE = ('track.py', 'gtc_common.py')
K1_CODE = ('mc_tracker.py', 'mc_common.py')
STATE = dict(events=None)
DIRECTIONS = dict(t=(False,), s=(False, True), b=(False, True), d=(False, True))  # False = forward, True = backward
RUN_ARMS = G.D_ARMS
SEED_ARM = dict(d='b')     # arm d carries b's seeds
EMBED_CHUNK = 32


def event(kind, **kw):
    rec = dict(time=G.utc(), event=kind, host=os.uname().nodename, pid=os.getpid(), **kw)
    line = getattr(json, '_a0_dumps', json.dumps)(rec, default=str)
    if STATE['events']:
        with open(STATE['events'], 'a') as f:
            f.write(line+'\n')
    print(line, flush=True)


def dense_index(dense):
    """{capture: manifest entry} of the dense manifest; anchors must be dense frames with slots 1..32 in order."""
    out = {}
    for c in dense['captures']:
        if c['status'] == 'OK':
            idx = [f['native_index'] for f in c['frames']]
            if idx != sorted(idx) or [f['position'] for f in c['frames']] != list(range(len(idx))):
                raise ValueError('dense frames out of order: '+c['capture'])
            if [f['slot'] for f in c['frames'] if f['is_anchor']] != list(range(1, 33)):
                raise ValueError('dense anchors are not slots 1..32: '+c['capture'])
        out[c['capture']] = c
    return out


def plan(seeds, arms, captures, dense):
    """[(arm, seeds capture entry, units, dense entry or None, skip reason or None)] in capture order. A capture whose dense entry
    is missing or not OK is skipped with its reason (reported, not substituted)."""
    caps = [c for c in seeds['captures'] if captures == 'all' or c['capture'] in captures]
    out = []
    for arm in arms:
        for c in sorted(caps, key=lambda c: c['capture']):
            us = [u for u in c['units'] if u['arm'] == SEED_ARM[arm]]
            d = dense.get(c['capture'])
            reason = None if d is not None and d['status'] == 'OK' else ('NOT_IN_DENSE_MANIFEST' if d is None else d['status'])
            if captures == 'all' and d is None:
                continue          # datasets outside the dense manifest (ARKit when absent) are not planned
            out.append((arm, c, us if reason is None else [], d if reason is None else None, reason))
    return out


def anchor_positions(d):
    """0-based dense positions of anchor slots 1..32."""
    pos = {f['slot']: f['position'] for f in d['frames'] if f['is_anchor']}
    return [pos[s] for s in range(1, 33)]


def forecast(seeds, arms, captures, dense):
    rows, total = [], K1['load_seconds']
    for arm, c, units, d, _ in plan(seeds, arms, captures, dense):
        if not units:
            continue
        n = len(d['frames']); of = len(units)*n
        sec = K1['overhead_per_unit'] + n*K1['embed_per_frame'] + of*K1['track_per_object_frame']
        rows.append(dict(arm=arm, capture=c['capture'], seeds=len(units), dense_frames=n, object_frames=of, seconds=sec,
                         gpu_gib=gpu_gib(n)))
        total += sec
    base = K1['peak_reserved_gib_64frames'] - 64*(FRAME_BYTES+IMAGE_BYTES)/2**30
    return dict(total_seconds=total, load_seconds=K1['load_seconds'], captures=len(rows), seeds=sum(r['seeds'] for r in rows),
                dense_frames=sum(r['dense_frames'] for r in rows), object_frames=sum(r['object_frames'] for r in rows),
                peak_gpu_gib=max((r['gpu_gib'] for r in rows), default=None), base_gib=base, rates=K1, rows=rows,
                note='seconds = overhead + dense frames x embed rate + seeds x dense frames x track rate (both directions); '
                     'GPU GiB = K1 base + dense frames x (cached features + stored tracker state)')


def gpu_gib(n):
    base = K1['peak_reserved_gib_64frames'] - 64*(FRAME_BYTES+IMAGE_BYTES)/2**30
    return base + n*(FRAME_BYTES+STATE_BYTES)/2**30


def contract(args, seeds_sha, frames_sha, dense_sha):
    code = {n: G.sha256_file(KIT/n) for n in CODE}
    code.update({'k1/'+n: G.sha256_file(G.K1_KIT/n) for n in K1_CODE})
    return dict(code=code, seeds_sha256=seeds_sha, frames_sha256=frames_sha, dense_sha256=dense_sha, device=args.device, anchors=32,
                embed_chunk=EMBED_CHUNK, directions={a: ['forward', 'backward'][:len(DIRECTIONS[a])] for a in RUN_ARMS})


def gtcb_sums():
    """{relative path: sha256} from lever6/gtcb/SHA256SUMS_GTCB (empty when absent)."""
    p = G.GTCB_OUT.parent/'SHA256SUMS_GTCB'
    if not p.is_file():
        return {}
    return {line.split(None, 1)[1].strip().lstrip('*'): line.split()[0] for line in p.read_text().splitlines() if line.strip()}


def assert_seed_copies(seeds):
    """The kit's seeds (out/seeds_b) are bit-identical to lever6/gtcb/out (SEEDS_GTCB.json and every npz). Returns a record."""
    sums = gtcb_sums(); checked = []
    pairs = [(G.SEEDS_B, G.SEEDS_B_ORIG, None)] + [(G.seed_copy(c['seeds_file']), Path(c['seeds_file']), c['seeds_sha256'])
                                                  for c in seeds['captures']]
    for copy, orig, pinned in pairs:
        got = G.sha256_file(copy)
        if pinned is not None and got != pinned:
            raise ValueError('seed copy differs from SEEDS_GTCB seeds_sha256: '+str(copy))
        if orig.is_file() and G.sha256_file(orig) != got:
            raise ValueError('seed copy differs from the gtcb original: '+str(copy))
        rel = str(orig.relative_to(G.GTCB_OUT.parent)) if str(orig).startswith(str(G.GTCB_OUT.parent)) else None
        if rel in sums and sums[rel] != got:
            raise ValueError('seed copy differs from SHA256SUMS_GTCB: '+rel)
        checked.append(dict(file=copy.name, sha256=got, original_present=orig.is_file(), in_sha256sums_gtcb=rel in sums))
    return dict(files=len(checked), originals_present=sum(c['original_present'] for c in checked),
                in_sha256sums_gtcb=sum(c['in_sha256sums_gtcb'] for c in checked), bit_identical=True)


def load_seed(path, unit):
    with np.load(path) as z:
        m240 = np.unpackbits(z[unit+'__240'], count=G.GRID[0]*G.GRID[1]).astype(bool).reshape(G.GRID)
        m480 = np.unpackbits(z[unit+'__480'], count=G.CANVAS[0]*G.CANVAS[1]).astype(bool).reshape(G.CANVAS)
    return m240, m480


def track_unit(carry, cache, seed_t, seed480, directions, keep=None):
    """K1 Sam3Carry.track with the propagation directions as a parameter: {t: (mask 480x640 or None, object score logit)}.
    keep: frame indices whose masks are kept (None = all); other frames keep only their score."""
    import torch
    tr = carry.tracker; n = len(cache)
    with torch.inference_mode():
        state = tr.init_state(cached_features=cache, video_height=G.CANVAS[0], video_width=G.CANVAS[1], num_frames=n,
                              offload_state_to_cpu=carry.device.type == 'cpu')
        tr.add_new_mask(state, frame_idx=int(seed_t), obj_id=1, mask=torch.from_numpy(np.asarray(seed480, bool)))
        tr.propagate_in_video_preflight(state, run_mem_encoder=True)
        result = {}
        for reverse in directions:
            for t, _, _, video_res, scores in tr.propagate_in_video(state, start_frame_idx=int(seed_t), max_frame_num_to_track=n,
                                                                     reverse=reverse, tqdm_disable=True):
                score = float(scores.reshape(-1)[0].float().cpu())
                mask = (video_res[0, 0] > 0).cpu().numpy() if keep is None or int(t) in keep else None
                result[int(t)] = (mask, score)
    want = set(range(seed_t, n)) if directions == (False,) else set(range(n))
    if set(result) != want:
        raise RuntimeError(f'tracker covered {len(result)} frames; expected {len(want)}')
    return result


def carried_masks(result, seed_slot, seed240, n):
    """(32,240,320) grid masks plus per-anchor scores/carried flags under K1's carry rule (result keyed by anchor 0..n-1)."""
    grid = np.zeros((32,)+G.GRID, bool); scores = [None]*32; carried = [False]*32; positive_empty = 0
    for t in range(n):
        slot = t+1
        if slot == seed_slot:
            grid[t] = seed240; carried[t] = True
            scores[t] = result[t][1] if t in result else None
            continue
        if t not in result:
            continue
        mask, score = result[t]
        scores[t] = score
        if not np.isfinite(score):
            raise ValueError('nonfinite tracker score')
        if score > 0:
            carried[t] = True
            m = G.canvas_to_grid(mask)
            positive_empty += not m.any()
            grid[t] = m
    return grid, scores, carried, positive_empty


def at_anchors(result, positions):
    """Dense-position results -> anchor-keyed results (0..31) for carried_masks."""
    return {k: result[p] for k, p in enumerate(positions) if p in result}


def embed_dense(carry, paths, shas):
    """K1 Sam3Carry.embed over chunks of EMBED_CHUNK frames, re-keyed 0..n-1; image kept on the host, position encoding shared."""
    import torch
    cache, pos, hw = {}, None, None
    for s in range(0, len(paths), EMBED_CHUNK):
        images = carry.frames(paths[s:s+EMBED_CHUNK], shas[s:s+EMBED_CHUNK])
        part, hw_ = carry.embed(images)
        del images
        if hw is None:
            hw = hw_
        elif hw_ != hw:
            raise ValueError('frame size differs across chunks')
        for k in sorted(part):
            img, out = part[k]
            tb = out['tracker_backbone_out']
            if pos is None:
                pos = tb['vision_pos_enc']
            elif not all(torch.equal(a, b) for a, b in zip(pos, tb['vision_pos_enc'])):
                raise ValueError('vision_pos_enc differs across chunks; cannot share it')
            tb['vision_pos_enc'] = pos
            cache[s+k] = (img.cpu(), out)
        del part
    if sorted(cache) != list(range(len(paths))):
        raise ValueError('embedding cache incomplete')
    return cache, hw


def pairing_check(dense_path, out):
    """Unit isolation: only the ScanNet manifest writes into out/track, and the ScanNet manifest never writes into out_ark/track."""
    scannet = Path(dense_path).resolve() == G.DENSE_MANIFEST.resolve()
    if not scannet and Path(out).resolve() == (G.OUT/'track').resolve():
        raise SystemExit('a non-ScanNet dense manifest may not write into the ScanNet unit\'s out/track')
    if scannet and Path(out).resolve() == (G.OUT_ARK/'track').resolve():
        raise SystemExit('the ScanNet dense manifest may not write into the ARKit unit\'s out_ark/track')


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--device', choices=['cuda', 'cpu'])
    ap.add_argument('--out', default=os.environ.get('GTCD_TRACK_OUT') or str(G.OUT/'track'))
    ap.add_argument('--arms', default='d', help="'d' (the only arm this kit runs)")
    ap.add_argument('--captures', default='all')
    ap.add_argument('--dense', default=os.environ.get('GTCD_DENSE') or str(G.DENSE_MANIFEST))
    ap.add_argument('--hard-stop', type=float, default=7000.)
    ap.add_argument('--rss-limit-gib', type=float, default=60.)
    ap.add_argument('--threads', type=int, default=8)
    ap.add_argument('--forecast', action='store_true')
    args = ap.parse_args(argv)
    arms = [a for a in RUN_ARMS if a in args.arms.split(',')]
    if not arms or set(args.arms.split(',')) - set(RUN_ARMS):
        raise SystemExit('--arms takes d')
    captures = 'all' if args.captures == 'all' else set(args.captures.split(','))
    seeds_path, frames_path, dense_path = G.SEEDS_B, G.FRAMES_PATH, Path(args.dense)
    seeds = G.read_json(seeds_path); frames = {c['capture']: c for c in G.read_json(frames_path)['captures']}
    dense = dense_index(G.read_json(dense_path))
    if captures != 'all' and captures - set(frames):
        raise SystemExit('--captures names captures outside the eligible population')
    if args.forecast:
        f = forecast(seeds, arms, captures, dense); f.pop('rows')
        print(json.dumps(f, indent=1)); return 0
    if args.device is None:
        raise SystemExit('--device required')
    out = Path(args.out).resolve()
    if not str(out).startswith('/scratch/') or not str(Path.cwd().resolve()).startswith('/scratch/'):
        raise SystemExit('runs from /scratch and writes to /scratch only')
    pairing_check(dense_path, out)
    out.mkdir(parents=True, exist_ok=True)
    STATE['events'] = out/'EVENTS.jsonl'
    if (out/'KILLED').exists():
        event('REFUSED', reason='a previous pass in this directory was killed; it is reported, not resumed'); return 3
    seed_check = assert_seed_copies(seeds)
    spec = contract(args, G.sha256_file(seeds_path), G.sha256_file(frames_path), G.sha256_file(dense_path))
    t0 = time.monotonic()

    def on_term(signum, frame):
        (out/'KILLED').write_text(f'{G.utc()} signal {signum}\n')
        event('KILLED', signal=signum, seconds=time.monotonic()-t0, note='finished capture files are the partial result')
        os._exit(128+signum)
    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(sig, on_term)
    work = plan(seeds, arms, captures, dense)
    fc = forecast(seeds, arms, captures, dense)
    event('START', device=args.device, arms=arms, captures=len(work), directions=spec['directions'], seed_copies=seed_check,
          skipped=[(c['capture'], r) for _, c, _, _, r in work if r], cuda_visible=os.environ.get('CUDA_VISIBLE_DEVICES'),
          contract=spec, forecast_seconds=fc['total_seconds'], forecast_peak_gpu_gib=fc['peak_gpu_gib'])
    try:
        return run(args, out, spec, seeds, frames, work, t0)
    except BaseException as e:
        event('FAILED', error=repr(e)[:800], seconds=time.monotonic()-t0)
        raise


def run(args, out, spec, seeds, frames, work, t0):
    import torch
    torch.set_num_threads(args.threads)
    sys.path.insert(1, str(G.K1_KIT))
    import mc_tracker as MT
    if args.device == 'cuda':
        if not torch.cuda.is_available():
            raise SystemExit('no CUDA device visible')
        if torch.cuda.get_device_capability(0) < (8, 0):
            event('REFUSED', reason='card without native bf16'); return 6
    carry = MT.Sam3Carry(args.device)
    if args.device == 'cuda' and carry.outside:
        event('REFUSED', reason='modules loaded from outside /scratch', modules=carry.outside[:20]); return 4
    from sam3.model.memory import SimpleMaskEncoder
    if not isinstance(carry.tracker.maskmem_backbone, SimpleMaskEncoder):
        event('REFUSED', reason='tracker memory encoder reads the image; host-side image cache not allowed'); return 5
    import psutil
    proc = psutil.Process()
    event('LOADED', load_seconds=carry.load_seconds, device=torch.cuda.get_device_name(0) if args.device == 'cuda' else 'cpu',
          card_bytes=torch.cuda.get_device_properties(0).total_memory if args.device == 'cuda' else None)
    done = {a: 0 for a in RUN_ARMS}; skipped = []; stopped = None; peak = 0.
    for arm, c, units, d, reason in work:
        cap = c['capture']
        if reason:
            skipped.append(dict(capture=cap, reason=reason)); continue
        path = out/arm/(G.stub(cap)+'.json.gz')
        if path.exists():
            if G.read_json(path).get('contract') != spec:
                raise SystemExit(f'{path} was written under another contract; move it aside (incompatible resume)')
            done[arm] += 1; continue
        if time.monotonic()-t0 > args.hard_stop:
            stopped = f'HARD_STOP before {arm} {cap}'; break
        u0 = time.monotonic()
        if args.device == 'cuda':
            torch.cuda.reset_peak_memory_stats()
        served = {f['slot']: f['sha256'] for f in frames[cap]['frames']}
        anchors = {f['slot']: f['sha256'] for f in d['frames'] if f['is_anchor']}
        if anchors != served:
            raise ValueError('dense anchors differ from FRAMES_GTC: '+cap)
        paths = [str(Path(args.dense).resolve().parent/d['dir']/f['file']) for f in d['frames']]
        shas = [f['sha256'] for f in d['frames']]
        positions = anchor_positions(d); n = len(paths)
        e0 = time.monotonic(); cache, hw = embed_dense(carry, paths, shas); embed_s = time.monotonic()-e0
        track_s = 0.; records = []; keep = set(positions)
        directions = DIRECTIONS[arm]
        for u in units:
            m240, m480 = load_seed(G.seed_copy(c['seeds_file']), u['unit'])
            if G.mask_sha(m240) != u['seed_sha256_240'] or G.mask_sha(m480) != u['seed_sha256_480']:
                raise ValueError('seed mask differs from SEEDS_GTCB: '+u['unit'])
            seed_pos = positions[u['seed_slot']-1]
            o0 = time.monotonic()
            result = track_unit(carry, cache, seed_pos, m480, directions, keep)
            grid, scores, carried, pe = carried_masks(at_anchors(result, positions), u['seed_slot'], m240, 32)
            sec = time.monotonic()-o0; track_s += sec
            dense_pos = sum(1 for p, (_, s) in result.items() if p != seed_pos and s > 0)
            records.append(dict(unit=u['unit'], arm=arm, seed_arm=SEED_ARM[arm], seed_slot=u['seed_slot'], seed_position=seed_pos,
                                seed_sha256_240=u['seed_sha256_240'], directions=['forward', 'backward'][:len(directions)],
                                tracked_frames=len(result), dense_positive_frames=dense_pos, scores=scores, carried=carried,
                                positive_empty=pe, masks=G.pack(grid), seconds=sec))
            if proc.memory_info().rss > args.rss_limit_gib*2**30:
                raise MemoryError(f'RSS above {args.rss_limit_gib} GiB')
        del cache
        gib = torch.cuda.max_memory_allocated()/2**30 if args.device == 'cuda' else None
        rgib = torch.cuda.max_memory_reserved()/2**30 if args.device == 'cuda' else None
        if args.device == 'cuda':
            torch.cuda.empty_cache()
        peak = max(peak, rgib or 0.)
        unit_s = time.monotonic()-u0
        G.write_json(path, dict(schema='gtcd-track-v1', contract=spec, capture=cap, arm=arm, tracker='sam3_video_tracker (K1 Sam3Carry)',
                                frames=[dict(slot=s, sha256=served[s]) for s in range(1, 33)], anchors=32, dense_frames=n,
                                anchor_positions=positions, dense_frames_sha256=G.digest(shas), units=records, skipped_units=[],
                                embed_seconds=embed_s, track_seconds=track_s, seconds=unit_s,
                                cuda_peak_alloc_gib=gib, cuda_peak_reserved_gib=rgib, rss_gib=proc.memory_info().rss/2**30,
                                peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20), gz=True)
        done[arm] += 1
        event('UNIT', arm=arm, capture=cap, seeds=len(units), dense_frames=n, embed_seconds=embed_s, track_seconds=track_s,
              seconds=unit_s, cuda_peak_alloc_gib=gib, cuda_peak_reserved_gib=rgib, elapsed=time.monotonic()-t0)
    total = {a: sum(1 for w in work if w[0] == a and not w[4]) for a in RUN_ARMS}
    G.write_json(out/'INDEX.json', dict(done=done, units=total, skipped=skipped, stopped=stopped, contract=spec,
                                        seconds=time.monotonic()-t0, load_seconds=carry.load_seconds,
                                        cuda_peak_reserved_gib=peak if args.device == 'cuda' else None))
    event('END', done=done, units=total, skipped=skipped, stopped=stopped, seconds=time.monotonic()-t0)
    return 0 if not stopped else 2


if __name__ == '__main__':
    sys.exit(main())
