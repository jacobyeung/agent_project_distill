"""GTC-B step 2 (GPU job, one 49 GB card; trinity-0-13 at normal priority): SAM 3 video tracker, arm b only, over each eligible
capture's 32 served anchors. Copy of the GTC kit's track.py with arm b added; t and s are not run here (their tracks are
lever6/gtc/out/track, read-only).

Tracker: sb_cachk/kit_v2/mc_tracker.Sam3Carry, imported unchanged (pinned checkpoint and sources verified on load; the same
build_sam3_video_model tracker, the same per-frame embedding, batch size 1, no detector). A unit is one (arm, capture): the
capture's frames are embedded once and every seed of the arm is carried over the cache one at a time.
Seeds: out/SEEDS_GTCB.json (arm b: the GT instance on its largest anchor). Frames: lever6/gtc/out/FRAMES_GTC.json (read-only).
Carry rule (K1 mc_track_io.object_record): the seed anchor keeps the seed mask itself; another anchor carries when the
tracker's object score is positive, with no other threshold; otherwise it is empty. b propagates forward and backward from its
seed (as s on K1 and GTC).
Masks: the tracker returns video-resolution 480x640 masks (K1 canvas); they reach relift's 240x320 grid by the served path
(resize to SHAPE, identity here, then [::2, ::2]). The seed anchor stores the exact 240x320 seed.
Outputs (all under --out on /scratch): b/<capture>.json.gz per unit (packed (32,240,320) masks, scores, timing, peak GPU
memory), EVENTS.jsonl, INDEX.json. Finished unit files are the partial result; a resume skips units whose file binds the
same contract and refuses one that does not; a pass killed by a signal records KILLED and is not resumed without an order.
Usage (SAM 3 interpreter /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python):
  python track.py --device cuda [--arms b] [--out ../out/track]
  python track.py --forecast                      (no torch; prints the GPU-second forecast from K1's rates)
  python track.py --device cpu --captures arkitscenes/41126645 --out ../out/rehearsal_cpu [--anchors 4]
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
CODE = ('track.py', 'gtc_common.py')
K1_CODE = ('mc_tracker.py', 'mc_common.py')
STATE = dict(events=None)
DIRECTIONS = dict(t=(False,), s=(False, True), b=(False, True))  # False = forward, True = backward
RUN_ARMS = G.B_ARMS


def event(kind, **kw):
    rec = dict(time=G.utc(), event=kind, host=os.uname().nodename, pid=os.getpid(), **kw)
    line = getattr(json, '_a0_dumps', json.dumps)(rec, default=str)
    if STATE['events']:
        with open(STATE['events'], 'a') as f:
            f.write(line+'\n')
    print(line, flush=True)


def plan(seeds, arms, captures, anchors):
    """[(arm, capture entry, units, skipped)] in arm-major order; units whose seed anchor lies beyond --anchors are skipped."""
    caps = [c for c in seeds['captures'] if captures == 'all' or c['capture'] in captures]
    out = []
    for arm in arms:
        for c in sorted(caps, key=lambda c: c['capture']):
            us = [u for u in c['units'] if u['arm'] == arm]
            out.append((arm, c, [u for u in us if u['seed_slot'] <= anchors], [u['unit'] for u in us if u['seed_slot'] > anchors]))
    return out


def object_frames(arm, slot, n):
    """Tracked object-frames of one seed over n frames, the unit K1's per-object-frame rate counts."""
    return n - slot + 1 if DIRECTIONS[arm] == (False,) else n


def forecast(seeds, arms, captures='all', anchors=32):
    rows, total = [], K1['load_seconds']
    for arm, c, units, _ in plan(seeds, arms, captures, anchors):
        if not units:
            continue
        of = sum(object_frames(arm, u['seed_slot'], anchors) for u in units)
        sec = K1['overhead_per_unit'] + anchors*K1['embed_per_frame'] + of*K1['track_per_object_frame']
        rows.append(dict(arm=arm, capture=c['capture'], seeds=len(units), object_frames=of, seconds=sec)); total += sec
    by_arm = {a: dict(units=sum(r['arm'] == a for r in rows), seeds=sum(r['seeds'] for r in rows if r['arm'] == a),
                      object_frames=sum(r['object_frames'] for r in rows if r['arm'] == a),
                      seconds=sum(r['seconds'] for r in rows if r['arm'] == a)) for a in arms}
    return dict(total_seconds=total, load_seconds=K1['load_seconds'], by_arm=by_arm, rates=K1,
                peak_memory_note='K1 measured %.2f GiB allocated / %.2f GiB reserved peak at 64 frames; 32 frames needs no more'
                % (K1['peak_alloc_gib_64frames'], K1['peak_reserved_gib_64frames']))


def contract(args, seeds_sha, frames_sha):
    code = {n: G.sha256_file(KIT/n) for n in CODE}
    code.update({'k1/'+n: G.sha256_file(G.K1_KIT/n) for n in K1_CODE})
    return dict(code=code, seeds_sha256=seeds_sha, frames_sha256=frames_sha, device=args.device, anchors=args.anchors,
                directions={a: ['forward', 'backward'][:len(DIRECTIONS[a])] for a in RUN_ARMS})


def load_seed(path, unit):
    with np.load(path) as z:
        m240 = np.unpackbits(z[unit+'__240'], count=G.GRID[0]*G.GRID[1]).astype(bool).reshape(G.GRID)
        m480 = np.unpackbits(z[unit+'__480'], count=G.CANVAS[0]*G.CANVAS[1]).astype(bool).reshape(G.CANVAS)
    return m240, m480


def track_unit(carry, cache, seed_t, seed480, directions):
    """K1 Sam3Carry.track with the propagation directions as a parameter: {t: (mask 480x640, object score logit)}."""
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
                result[int(t)] = ((video_res[0, 0] > 0).cpu().numpy(), float(scores.reshape(-1)[0].float().cpu()))
    want = set(range(seed_t, n)) if directions == (False,) else set(range(n))
    if set(result) != want:
        raise RuntimeError(f'tracker covered frames {sorted(result)}; expected {sorted(want)}')
    return result


def carried_masks(result, seed_slot, seed240, n):
    """(32,240,320) grid masks plus per-anchor scores/carried flags under K1's carry rule."""
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


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--device', choices=['cuda', 'cpu'])
    ap.add_argument('--out', default=str(G.OUT/'track'))
    ap.add_argument('--arms', default='b', help="'b' (the only arm this kit runs)")
    ap.add_argument('--captures', default='all')
    ap.add_argument('--anchors', type=int, default=32, help='track only anchors 1..N (CPU rehearsal); 32 = all served anchors')
    ap.add_argument('--hard-stop', type=float, default=3600.)
    ap.add_argument('--rss-limit-gib', type=float, default=40.)
    ap.add_argument('--threads', type=int, default=8)
    ap.add_argument('--forecast', action='store_true')
    args = ap.parse_args(argv)
    arms = [a for a in RUN_ARMS if a in args.arms.split(',')]
    if not arms or set(args.arms.split(',')) - set(RUN_ARMS):
        raise SystemExit('--arms takes b')
    if not 1 <= args.anchors <= 32:
        raise SystemExit('--anchors must be 1..32')
    captures = 'all' if args.captures == 'all' else set(args.captures.split(','))
    seeds_path, frames_path = G.SEEDS_B, G.FRAMES_PATH
    seeds = G.read_json(seeds_path); frames = {c['capture']: c for c in G.read_json(frames_path)['captures']}
    if captures != 'all' and captures - set(frames):
        raise SystemExit('--captures names captures outside the eligible population')
    if args.forecast:
        print(json.dumps(forecast(seeds, arms, captures, args.anchors), indent=1)); return 0
    if args.device is None:
        raise SystemExit('--device required')
    out = Path(args.out).resolve()
    if not str(out).startswith('/scratch/'):
        raise SystemExit('results go to /scratch only')
    out.mkdir(parents=True, exist_ok=True)
    STATE['events'] = out/'EVENTS.jsonl'
    if (out/'KILLED').exists():
        event('REFUSED', reason='a previous pass in this directory was killed; it is reported, not resumed'); return 3
    spec = contract(args, G.sha256_file(seeds_path), G.sha256_file(frames_path))
    t0 = time.monotonic()

    def on_term(signum, frame):
        (out/'KILLED').write_text(f'{G.utc()} signal {signum}\n')
        event('KILLED', signal=signum, seconds=time.monotonic()-t0, note='finished unit files are the partial result')
        os._exit(128+signum)
    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(sig, on_term)
    work = plan(seeds, arms, captures, args.anchors)
    event('START', device=args.device, arms=arms, units=len(work), anchors=args.anchors, directions=spec['directions'],
          cuda_visible=os.environ.get('CUDA_VISIBLE_DEVICES'), contract=spec,
          forecast_seconds=forecast(seeds, arms, captures, args.anchors)['total_seconds'])
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
    import psutil
    proc = psutil.Process()
    event('LOADED', load_seconds=carry.load_seconds, device=torch.cuda.get_device_name(0) if args.device == 'cuda' else 'cpu',
          card_bytes=torch.cuda.get_device_properties(0).total_memory if args.device == 'cuda' else None)
    done = {a: 0 for a in RUN_ARMS}; stopped = None; peak = 0.
    for arm, c, units, skipped in work:
        cap = c['capture']; path = out/arm/(G.stub(cap)+'.json.gz')
        if path.exists():
            if G.read_json(path).get('contract') != spec:
                raise SystemExit(f'{path} was written under another contract; move it aside (incompatible resume)')
            done[arm] += 1; continue
        if time.monotonic()-t0 > args.hard_stop:
            stopped = f'HARD_STOP before {arm} {cap}'; break
        u0 = time.monotonic()
        if args.device == 'cuda':
            torch.cuda.reset_peak_memory_stats()
        fr = frames[cap]['frames'][:args.anchors]
        if [f['slot'] for f in fr] != list(range(1, args.anchors+1)):
            raise ValueError('anchor order differs: '+cap)
        embed_s = track_s = 0.; records = []
        if units:
            images = carry.frames([f['path'] for f in fr], [f['sha256'] for f in fr])
            e0 = time.monotonic(); cache, hw = carry.embed(images); embed_s = time.monotonic()-e0
            del images
            directions = DIRECTIONS[arm]
            for u in units:
                m240, m480 = load_seed(c['seeds_file'], u['unit'])
                if G.mask_sha(m240) != u['seed_sha256_240'] or G.mask_sha(m480) != u['seed_sha256_480']:
                    raise ValueError('seed mask differs from SEEDS_GTCB: '+u['unit'])
                o0 = time.monotonic()
                result = track_unit(carry, cache, u['seed_slot']-1, m480, directions)
                grid, scores, carried, pe = carried_masks(result, u['seed_slot'], m240, len(fr))
                sec = time.monotonic()-o0; track_s += sec
                records.append(dict(unit=u['unit'], arm=arm, seed_slot=u['seed_slot'], seed_sha256_240=u['seed_sha256_240'],
                                    directions=['forward', 'backward'][:len(directions)], tracked_frames=len(result),
                                    scores=scores, carried=carried, positive_empty=pe, masks=G.pack(grid), seconds=sec))
                if proc.memory_info().rss > args.rss_limit_gib*2**30:
                    raise MemoryError(f'RSS above {args.rss_limit_gib} GiB')
            del cache
        gib = torch.cuda.max_memory_allocated()/2**30 if args.device == 'cuda' else None
        rgib = torch.cuda.max_memory_reserved()/2**30 if args.device == 'cuda' else None
        peak = max(peak, rgib or 0.)
        unit_s = time.monotonic()-u0
        G.write_json(path, dict(schema='gtcb-track-v1', contract=spec, capture=cap, arm=arm, tracker='sam3_video_tracker (K1 Sam3Carry)',
                                frames=[dict(slot=f['slot'], sha256=f['sha256']) for f in fr], anchors=args.anchors,
                                units=records, skipped_units=skipped, embed_seconds=embed_s, track_seconds=track_s, seconds=unit_s,
                                cuda_peak_alloc_gib=gib, cuda_peak_reserved_gib=rgib, rss_gib=proc.memory_info().rss/2**30,
                                peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20), gz=True)
        done[arm] += 1
        event('UNIT', arm=arm, capture=cap, seeds=len(units), skipped=len(skipped), embed_seconds=embed_s, track_seconds=track_s,
              seconds=unit_s, cuda_peak_alloc_gib=gib, cuda_peak_reserved_gib=rgib, elapsed=time.monotonic()-t0)
    total = {a: sum(1 for w in work if w[0] == a) for a in RUN_ARMS}
    G.write_json(out/'INDEX.json', dict(done=done, units=total, stopped=stopped, contract=spec, seconds=time.monotonic()-t0,
                                        load_seconds=carry.load_seconds, cuda_peak_reserved_gib=peak if args.device == 'cuda' else None))
    event('END', done=done, units=total, stopped=stopped, seconds=time.monotonic()-t0)
    return 0 if not stopped else 2


if __name__ == '__main__':
    sys.exit(main())
