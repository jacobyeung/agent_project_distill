"""Tracker pass, capture-major: embed a capture's 64 dense frames once, then carry every seed set in ORDER.

Resumes per (seed set, frame set, capture) when the stored contract matches; keeps a cumulative budget ledger across
resumes; projects the total after --project-after captures (and every 10 after) and drops trailing sets in ORDER while
the projection exceeds --hard-stop; stops if S_A0/D64 alone cannot fit. SIGTERM is recorded as KILLED, never retried.
Usage (SAM 3 interpreter):
  python mc_track_pass.py --device cuda [--out ../out/track]
  python mc_track_pass.py --device cpu --out ../out/dry/track_cpu --captures arkitscenes/41048124 --max-frames 8 --sets S_A0/D64
"""
import argparse, json, os, signal, sys, time
from pathlib import Path
import numpy as np
import mc_common as C
import mc_track_io as IO

CODE = ('mc_common.py', 'mc_tracker.py', 'mc_track_io.py', 'mc_track_pass.py')
STATE = dict(events=None)


def event(kind, **kw):
    rec = dict(time=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), event=kind, host=os.uname().nodename, pid=os.getpid(), **kw)
    with open(STATE['events'], 'a') as f:
        f.write(json.dumps(rec)+'\n')
    print(json.dumps(rec), flush=True)


def ledger_path(out):
    return Path(out)/'BUDGET.json'


def read_ledger(out):
    p = ledger_path(out)
    return json.loads(p.read_text()) if p.exists() else dict(spent_seconds=0., runs=[], dropped=[], stopped=None)


def save_ledger(out, ledger):
    tmp = ledger_path(out).with_suffix('.tmp')
    tmp.write_text(json.dumps(ledger, indent=1))
    os.replace(tmp, ledger_path(out))


def project(spent, remaining, embed_mean, set_means, sets):
    """Projected cumulative seconds if `sets` run on every remaining capture."""
    return spent + remaining*(embed_mean + sum(set_means.get(s, 0.) for s in sets))


def plan_drop(spent, remaining, embed_mean, set_means, sets, cap):
    """Trailing sets (in ORDER) to drop so the projection fits the cap; None when even the first set does not fit."""
    keep = list(sets)
    while keep and project(spent, remaining, embed_mean, set_means, keep) > cap:
        keep.pop()
    if not keep:
        return None
    return [s for s in sets if s not in keep]


def contract(args, frame_sets_sha):
    return dict(checkpoint=C.CHECKPOINT_SHA256, code={n: C.sha256_file(C.KIT/n) for n in CODE}, frame_sets=frame_sets_sha,
                device=args.device, max_frames=args.max_frames)


def seed_digest(seed_set, entry, seed_masks):
    """sha256 over one seed set's masks of a capture, so a resume checks each set against its own seeds."""
    import hashlib
    h = hashlib.sha256()
    for o in entry['objects']:
        key = f"{seed_set}_{o['k']}"
        h.update(key.encode())
        if key in seed_masks:
            h.update(np.packbits(seed_masks[key].reshape(-1)).tobytes())
    return h.hexdigest()


def timing_receipt(out, run, worked, embed_times, set_times, sets, remaining, projection, drop, cap, spent_now):
    """TIMING_RECEIPT.json after the first captures of S_A0/D64: measured means and the projection, before continuing."""
    means = {s: float(np.mean(v)) for s, v in set_times.items() if v}
    body = dict(device=run['device'], host=run['host'], load_seconds=run['load_seconds'], captures_measured=worked,
                embed_mean_seconds=float(np.mean(embed_times)), set_mean_seconds=means, sets=sets, remaining_captures=remaining,
                spent_seconds=spent_now, projected_seconds=projection, projected_gpu_hours=projection/3600, hard_stop_seconds=cap,
                dropped=drop, decision='stop: S_A0/D64 alone exceeds the hard stop' if drop is None else
                f'continue; drop {drop}' if drop else 'continue with every set')
    for dest in {Path(out)/'TIMING_RECEIPT.json', C.OUT/'TIMING_RECEIPT.json'} if Path(out) == C.OUT/'track' else {Path(out)/'TIMING_RECEIPT.json'}:
        C.write_json(dest, body)
    return body


def window(dense_n, center, size):
    lo = max(0, min(center - size//2, dense_n - size))
    return list(range(lo, lo+size))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--device', required=True, choices=['cuda', 'cpu'])
    ap.add_argument('--out', default=str(C.OUT/'track'))
    ap.add_argument('--captures', default='all')
    ap.add_argument('--sets', default=','.join(C.ORDER))
    ap.add_argument('--max-frames', type=int, default=0)
    ap.add_argument('--hard-stop', type=float, default=7200.)
    ap.add_argument('--project-after', type=int, default=10)
    ap.add_argument('--rss-limit-gib', type=float, default=40.)
    ap.add_argument('--exclude-withheld', action='store_true', help='skip the K1-train captures in the 80 withheld rooms (GUARD.json)')
    ap.add_argument('--resume-after-stop', action='store_true', help='operator decision only: continue a pass the ledger records as stopped')
    args = ap.parse_args(argv)
    C.local(C.ROOT)
    out = Path(args.out).resolve()
    if not str(out).startswith('/scratch/'):
        raise SystemExit('results go to /scratch only')
    out.mkdir(parents=True, exist_ok=True)
    STATE['events'] = out/'EVENTS.jsonl'
    t_start = time.monotonic()
    ledger = read_ledger(out)
    if ledger.get('stopped'):
        if not args.resume_after_stop:
            event('REFUSED', reason=f"ledger records a stop ({ledger['stopped']}); a stopped or killed pass is reported, not rerun")
            return 3
        ledger.setdefault('resumed_stops', []).append(ledger['stopped'])
        ledger['stopped'] = None

    def on_term(signum, frame):
        ledger['spent_seconds'] = STATE.get('spent0', 0.) + time.monotonic() - t_start
        ledger['stopped'] = f'KILLED by signal {signum}'
        save_ledger(out, ledger)
        event('KILLED', signal=signum, spent_seconds=ledger['spent_seconds'])
        os._exit(128+signum)
    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGHUP, on_term)

    frame_sets_sha = C.pin(C.OUT/'FRAME_SETS.json')
    C.pin(C.OUT/'seeds/SEEDS.json')
    frame_sets = C.frame_sets()
    seeds = C.read_json(C.OUT/'seeds/SEEDS.json')
    entries = {r['capture']: r for r in seeds['captures']}
    phr = seeds['summary']['S_PHR']['status']
    sets = [s for s in args.sets.split(',') if s in C.ORDER and (not s.startswith('S_PHR') or phr == 'PRESENT')]
    skipped = [s for s in args.sets.split(',') if s not in sets]
    sets = [s for s in sets if s not in ledger['dropped']]
    caps = sorted(entries) if args.captures == 'all' else args.captures.split(',')
    excluded = []
    if args.exclude_withheld:
        excluded = sorted(set(caps) & set(C.read_json(C.OUT/'GUARD.json')['lists']['withheld_80']['hit_captures']))
        caps = [k for k in caps if k not in excluded]
    spec = contract(args, frame_sets_sha)
    STATE['spent0'] = spent0 = ledger['spent_seconds']
    event('START', device=args.device, sets=sets, skipped=skipped, dropped=ledger['dropped'], captures=len(caps), excluded=excluded,
          spent_seconds=spent0, hard_stop=args.hard_stop, contract=spec, cuda_visible=os.environ.get('CUDA_VISIBLE_DEVICES'))

    import mc_tracker as MT
    import torch
    if args.device == 'cuda' and not torch.cuda.is_available():
        raise SystemExit('no CUDA device visible')
    tracker = MT.Sam3Carry(args.device)
    if args.device == 'cuda' and tracker.outside:
        event('REFUSED', reason='modules loaded from outside /scratch', modules=tracker.outside[:20])
        return 4
    base = dict(C.PINS)
    run = dict(started=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), host=os.uname().nodename, load_seconds=tracker.load_seconds,
               device=torch.cuda.get_device_name(0) if args.device == 'cuda' else 'cpu', captures=0)
    ledger['runs'].append(run)
    embed_times, set_times, worked = [], {s: [] for s in sets}, 0
    import psutil
    proc = psutil.Process()

    def spent():
        return spent0 + time.monotonic() - t_start

    def todo(canonical):
        need, masks = [], None
        for s in sets:
            seed_set, fs = s.split('/')
            p = IO.track_path(seed_set, fs, canonical, out)
            if p.exists():
                have = C.read_json(p)
                if have.get('contract') != spec:
                    raise SystemExit(f'{p} was written under another contract; move it aside before resuming')
                masks = IO.load_seeds(canonical) if masks is None else masks
                if have.get('seed_digest') != seed_digest(seed_set, entries[canonical], masks):
                    raise SystemExit(f'{p} was carried from other {seed_set} seeds; move it aside before resuming')
                continue
            need.append(s)
        return need

    for ci, canonical in enumerate(caps):
        need = todo(canonical)
        if not need:
            continue
        if spent() + (np.mean(embed_times) if embed_times else 0.) + sum(np.mean(set_times[s]) if set_times[s] else 0. for s in need) > args.hard_stop:
            ledger['stopped'] = f'HARD_STOP before {canonical}'
            break
        c0 = time.monotonic()
        C.PINS.clear(); C.PINS.update(base)
        fsr = frame_sets['captures'][canonical]
        entry = entries[canonical]
        C.PINS[str(C.OUT/'seeds'/(C.stub(canonical)+'.npz'))] = entry['seeds_sha256']
        seed_masks = IO.load_seeds(canonical)
        dense = fsr['dense']
        slots = list(range(len(dense)))
        if args.max_frames:
            lead = need[0].split('/')[0]
            first = next((o for o in entry['objects'] if o[lead]['status'] == 'OK'), None)
            centre = fsr['A32'][first[lead]['slot']-1] if first else 0
            slots = window(len(dense), centre, args.max_frames)
        images = tracker.frames([dense[i]['path'] for i in slots], [dense[i]['sha256'] for i in slots])
        for i in slots:
            C.PINS[dense[i]['path']] = dense[i]['sha256']
        e0 = time.monotonic()
        cache, hw = tracker.embed(images)
        embed_s = time.monotonic() - e0
        embed_times.append(embed_s)
        local = {d: j for j, d in enumerate(slots)}
        written = {}

        def a0_record(fs, k):
            if ('S_A0', fs) not in written:
                p = IO.track_path('S_A0', fs, canonical, out)
                written[('S_A0', fs)] = {r['k']: r for r in C.read_json(p)['objects']} if p.exists() else {}
            return written[('S_A0', fs)].get(k)
        for s in need:
            seed_set, fs = s.split('/')
            s0 = time.monotonic()
            frames = slots if fs == 'D64' else [d for d in fsr['A32'] if d in local]
            sub = {j: cache[local[d]] for j, d in enumerate(frames)}
            pos = {d: j for j, d in enumerate(frames)}
            anchor_pos = [pos.get(d) for d in fsr['A32']]
            objects, skipped_objects = [], []
            for o in entry['objects']:
                seed = o[seed_set]
                if seed['status'] != 'OK':
                    continue
                t_seed = anchor_pos[seed['slot']-1]
                if t_seed is None:
                    skipped_objects.append(dict(name=o['name'], reason='seed anchor outside the tracked frames'))
                    continue
                if seed_set == 'S_PHR' and seed.get('same_as_S_A0'):
                    twin = a0_record(fs, o['k'])
                    if twin is not None:
                        objects.append(dict(twin, reused_from='S_A0', seconds=0.))
                        continue
                mask = seed_masks[f"{seed_set}_{o['k']}"]
                o0 = time.monotonic()
                result = tracker.track(sub, t_seed, mask)
                rec = IO.object_record(o['k'], o['name'], o['instance'], seed['slot'], frames, anchor_pos, result, mask)
                rec['seconds'] = time.monotonic() - o0
                objects.append(rec)
                if proc.memory_info().rss > args.rss_limit_gib*2**30:
                    raise MemoryError(f'RSS above {args.rss_limit_gib} GiB')
            secs = time.monotonic() - s0
            set_times[s].append(secs)
            if seed_set == 'S_A0':
                written[('S_A0', fs)] = {r['k']: r for r in objects}
            C.write_json(IO.track_path(seed_set, fs, canonical, out),
                         dict(capture=canonical, seed_set=seed_set, frame_set=fs, tracker='sam3_video_tracker', status='OK',
                              contract=spec, seed_digest=seed_digest(seed_set, entry, seed_masks), dense_slots=frames, embed_seconds=embed_s, seconds=secs, objects=objects,
                              skipped_objects=skipped_objects, partial=bool(args.max_frames), native_hw=list(hw),
                              cuda_peak_gib=torch.cuda.max_memory_allocated()/2**30 if args.device == 'cuda' else None,
                              peak_rss_gib=proc.memory_info().rss/2**30), gz=True)
        del cache, images
        worked += 1
        run['captures'] = worked
        ledger['spent_seconds'] = spent()
        save_ledger(out, ledger)
        event('CAPTURE', capture=canonical, index=ci, sets=need, embed_seconds=embed_s,
              set_seconds={s: set_times[s][-1] for s in need}, seconds=time.monotonic()-c0, spent_seconds=ledger['spent_seconds'])
        if worked >= args.project_after and (worked - args.project_after) % 10 == 0:
            remaining = sum(bool(todo(k)) for k in caps[ci+1:])
            means = {s: float(np.mean(v)) for s, v in set_times.items() if v}
            projection = project(spent(), remaining, float(np.mean(embed_times)), means, sets)
            drop = plan_drop(spent(), remaining, float(np.mean(embed_times)), means, sets, args.hard_stop)
            event('PROJECTION', after=worked, remaining=remaining, projected_seconds=projection, embed_mean=float(np.mean(embed_times)),
                  set_means=means, drop=drop)
            if worked == args.project_after:
                timing_receipt(out, run, worked, embed_times, set_times, sets, remaining, projection, drop, args.hard_stop, spent())
            if drop is None:
                ledger['stopped'] = f'PROJECTION: {sets[0]} alone exceeds {args.hard_stop} s'
                break
            if drop:
                ledger['dropped'] += drop
                sets = [s for s in sets if s not in drop]
    ledger['spent_seconds'] = spent()
    save_ledger(out, ledger)
    C.PINS.clear(); C.PINS.update(base); C.code_pins()
    done = {s: sum(IO.track_path(*s.split('/'), k, out).exists() for k in caps) for s in C.ORDER}
    C.write_json(out/'TRACK_INDEX.json', dict(sets_run=sets, dropped=ledger['dropped'], skipped=skipped, stopped=ledger['stopped'],
                                              captures=len(caps), excluded=excluded, done=done, spent_seconds=ledger['spent_seconds'], contract=spec,
                                              embed_mean=float(np.mean(embed_times)) if embed_times else None,
                                              set_means={s: float(np.mean(v)) for s, v in set_times.items() if v}))
    event('END', stopped=ledger['stopped'], done=done, spent_seconds=ledger['spent_seconds'], seconds=time.monotonic()-t_start)
    return 0 if not ledger['stopped'] else 2


if __name__ == '__main__':
    sys.exit(main())
