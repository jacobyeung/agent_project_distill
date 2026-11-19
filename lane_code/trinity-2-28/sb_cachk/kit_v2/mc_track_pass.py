"""Tracker pass in the registered global arm order (C.ORDER): S_A0/D64 on every capture, then S_GT/D64, then the A32
sets, then S_PHR. Each (arm, capture) unit embeds the frames its arm reads (D64: the dense frames; A32: the anchors) and
carries every seed of that arm, so a capture is embedded once per arm; the projection counts those repeated embeddings.
An S_PHR seed equal to its S_A0 seed reuses the S_A0 record, and a unit with nothing to track embeds nothing.

Population: out/v2/POPULATION.json (RULING 1056Z); each arm runs its 204 decision captures first, then the five
withheld-room captures that complete the 209 reported beside them.
Ledger <out>/BUDGET.json keeps the cumulative budget and binds the population id and the code contract; each carried
file binds the population id, its frames, its seed metadata and its seed mask bytes. A resume that differs in any of
them is refused. A pass the ledger records as KILLED, or one that left the ledger active with no exit record, is
reported and never resumed; --resume-after-stop applies only to HARD_STOP and PROJECTION stops. Elapsed seconds are
saved after every unit and on every exit, exceptions included.
Projection: after the first --project-after S_A0/D64 captures, <out>/TIMING_RECEIPT.json records the measured rates and
the projected total; then every 10 units the trailing sets in C.ORDER are dropped while the projection exceeds
--hard-stop, and the pass stops when S_A0/D64 alone cannot fit.
Usage (SAM 3 interpreter):
  python mc_track_pass.py --device cuda [--out ../out/v2/track]
  python mc_track_pass.py --device cpu --out ../out/v2/dry/track_cpu_full --captures arkitscenes/41048124 --project-after 1
"""
import argparse, hashlib, json, os, resource, signal, sys, time
from pathlib import Path
import numpy as np
import mc_common as C
import mc_track_io as IO

CODE = ('mc_common.py', 'mc_tracker.py', 'mc_track_io.py', 'mc_track_pass.py')
STATE = dict(events=None)
RESUMABLE = ('HARD_STOP', 'PROJECTION')


def event(kind, **kw):
    rec = dict(time=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), event=kind, host=os.uname().nodename, pid=os.getpid(), **kw)
    with open(STATE['events'], 'a') as f:
        f.write(json.dumps(rec)+'\n')
    print(json.dumps(rec), flush=True)


def ledger_path(out):
    return Path(out)/'BUDGET.json'


def new_ledger():
    return dict(spent_seconds=0., runs=[], dropped=[], stopped=None, binding=None, active=None, failures=[],
                rates=dict(units=0, unit_seconds=0., embed_seconds=0., embed_frames=0, track_seconds=0., object_frames=0),
                a0_d64_units=0, receipt=None)


def read_ledger(out):
    p = ledger_path(out)
    return dict(new_ledger(), **json.loads(p.read_text())) if p.exists() else new_ledger()


def save_ledger(out, ledger):
    tmp = ledger_path(out).with_suffix('.tmp')
    tmp.write_text(json.dumps(ledger, indent=1))
    os.replace(tmp, ledger_path(out))


def refusal(ledger, resume_after_stop):
    """Reason the ledger forbids this start, or None. KILLED has no override."""
    stop, active = ledger.get('stopped'), ledger.get('active')
    if stop and str(stop).startswith('KILLED'):
        return f'ledger records {stop}; a killed pass is reported, never resumed'
    if active:
        return (f"ledger was left active by pid {active.get('pid')} on {active.get('host')} with no exit record; "
                'treated as KILLED: reported, never resumed')
    if stop and not (resume_after_stop and str(stop).startswith(RESUMABLE)):
        return f'ledger records a stop ({stop}); only an operator --resume-after-stop continues a HARD_STOP or PROJECTION stop'
    return None


def rates(ledger):
    """Measured seconds per embedded frame, per tracked object-frame and per unit (overhead), or None before any unit."""
    r = ledger['rates']
    if not r['units']:
        return None
    embed = r['embed_seconds']/r['embed_frames'] if r['embed_frames'] else 0.
    track = r['track_seconds']/r['object_frames'] if r['object_frames'] else 0.
    return dict(embed_per_frame=embed, track_per_object_frame=track,
                overhead_per_unit=max(0., (r['unit_seconds']-r['embed_seconds']-r['track_seconds'])/r['units']))


def unit_cost(rate, n_frames, n_objects):
    """Predicted seconds of one unit: its own embedding of n_frames plus n_objects carried over them."""
    if rate is None or not n_objects:
        return 0.
    return rate['overhead_per_unit'] + n_frames*rate['embed_per_frame'] + n_objects*n_frames*rate['track_per_object_frame']


def project(spent, remaining, sets):
    """Projected cumulative seconds if every remaining unit of `sets` runs; remaining = {set: predicted seconds}."""
    return spent + sum(remaining.get(s, 0.) for s in sets)


def plan_drop(spent, remaining, sets, cap):
    """Trailing sets (in ORDER) to drop so the projection fits the cap; None when even the first set does not fit."""
    keep = list(sets)
    while keep and project(spent, remaining, keep) > cap:
        keep.pop()
    if not keep:
        return None
    return [s for s in sets if s not in keep]


def units(sets, caps):
    """Global arm order: every capture of one set before the next set."""
    return [(s, c) for s in sets for c in caps]


def contract(args, population_id):
    return dict(checkpoint=C.CHECKPOINT_SHA256, code={n: C.sha256_file(C.KIT/n) for n in CODE}, device=args.device,
                max_frames=args.max_frames, population_id=population_id)


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def seed_digest(seed_set, entry, seed_masks):
    """sha256 over one seed set's masks of a capture, so a resume checks each set against its own seeds."""
    h = hashlib.sha256()
    for o in entry['objects']:
        key = f"{seed_set}_{o['k']}"
        h.update(key.encode())
        if key in seed_masks:
            h.update(np.packbits(seed_masks[key].reshape(-1)).tobytes())
    return h.hexdigest()


def seed_meta_digest(seed_set, entry):
    """sha256 over the seed set's per-object metadata (operand, instance, status, anchor, reuse of S_A0)."""
    return digest([[o['k'], o['name'], o['instance'], o[seed_set]['status'], o[seed_set].get('slot'),
                    o[seed_set].get('same_as_S_A0')] for o in entry['objects']])


def timing_receipt(out, body):
    """TIMING_RECEIPT.json in the track directory only (the CPU summary publishes it to out/v2 after the pass)."""
    C.write_json(Path(out)/'TIMING_RECEIPT.json', body)
    return body


def window(dense_n, center, size):
    lo = max(0, min(center - size//2, dense_n - size))
    return list(range(lo, lo+size))


def capture_slots(fsr, entry, max_frames):
    """Dense slots the capture's units read: all of them, or a window round the first S_A0 (else S_GT) seed anchor."""
    dense = fsr['dense']
    if not max_frames:
        return list(range(len(dense)))
    first = next((o['S_A0'] for o in entry['objects'] if o['S_A0']['status'] == 'OK'),
                 next((o['S_GT'] for o in entry['objects'] if o['S_GT']['status'] == 'OK'), None))
    return window(len(dense), fsr['A32'][first['slot']-1] if first else 0, max_frames)


def plan_unit(seed_set, fs, fsr, entry, slots, twin_exists):
    """(frames, anchor_pos, track, reuse, skipped) of one unit: frames are dense slots in time order."""
    frames = list(slots) if fs == 'D64' else [d for d in fsr['A32'] if d in set(slots)]
    pos = {d: j for j, d in enumerate(frames)}
    anchor_pos = [pos.get(d) for d in fsr['A32']]
    track, reuse, skipped = [], [], []
    for o in entry['objects']:
        seed = o[seed_set]
        if seed['status'] != 'OK':
            continue
        if anchor_pos[seed['slot']-1] is None:
            skipped.append(dict(name=o['name'], reason='seed anchor outside the tracked frames'))
        elif seed_set == 'S_PHR' and seed.get('same_as_S_A0') and twin_exists:
            reuse.append(o)
        else:
            track.append(o)
    return frames, anchor_pos, track, reuse, skipped


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--device', required=True, choices=['cuda', 'cpu'])
    ap.add_argument('--out', default=str(C.OUT/'track'))
    ap.add_argument('--captures', default='all', help='comma-separated subset of the population (CPU checks)')
    ap.add_argument('--sets', default=','.join(C.ORDER))
    ap.add_argument('--max-frames', type=int, default=0)
    ap.add_argument('--hard-stop', type=float, default=7200.)
    ap.add_argument('--project-after', type=int, default=10)
    ap.add_argument('--rss-limit-gib', type=float, default=40.)
    ap.add_argument('--resume-after-stop', action='store_true',
                    help='operator decision only: continue a HARD_STOP or PROJECTION stop; never a KILLED pass')
    args = ap.parse_args(argv)
    C.local(C.ROOT)
    out = Path(args.out).resolve()
    if not str(out).startswith('/scratch/'):
        raise SystemExit('results go to /scratch only')
    C.scoring_guard(C.OUT, out)
    out.mkdir(parents=True, exist_ok=True)
    STATE['events'] = out/'EVENTS.jsonl'
    t_start = time.monotonic()
    ledger = read_ledger(out)
    reason = refusal(ledger, args.resume_after_stop)
    if reason:
        event('REFUSED', reason=reason)
        return 3
    if ledger.get('stopped'):
        ledger.setdefault('resumed_stops', []).append(ledger['stopped'])
        ledger['stopped'] = None
    spent0 = float(ledger['spent_seconds'])

    def spent():
        return spent0 + time.monotonic() - t_start

    def on_term(signum, frame):
        ledger['spent_seconds'] = spent()
        ledger['stopped'] = f'KILLED by signal {signum}'
        ledger['active'] = None
        save_ledger(out, ledger)
        event('KILLED', signal=signum, spent_seconds=ledger['spent_seconds'])
        os._exit(128+signum)
    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(sig, on_term)

    pop = C.population()
    spec = contract(args, pop['population_id'])
    binding = dict(population_id=pop['population_id'], contract=spec)
    if ledger.get('binding') not in (None, binding):
        event('REFUSED', reason='incompatible resume: the ledger was written under another population or code contract',
              ledger_binding=ledger['binding'], binding=binding)
        return 5
    ledger['binding'] = binding
    ledger['active'] = dict(pid=os.getpid(), host=os.uname().nodename, started=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    save_ledger(out, ledger)
    try:
        return run(args, out, ledger, pop, spec, spent, t_start)
    except BaseException as e:
        ledger['failures'].append(dict(time=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), error=repr(e)[:500]))
        event('FAILED', error=repr(e)[:500], spent_seconds=spent())
        raise
    finally:
        ledger['spent_seconds'] = spent()
        ledger['active'] = None
        save_ledger(out, ledger)


def run(args, out, ledger, pop, spec, spent, t_start):
    C.pin(C.OUT/'FRAME_SETS.json')
    C.pin(C.OUT/'seeds/SEEDS.json')
    frame_sets = C.frame_sets()
    seeds = C.read_json(C.OUT/'seeds/SEEDS.json')
    entries = {r['capture']: r for r in seeds['captures']}
    phr = seeds['summary']['S_PHR']['status']
    asked = [s for s in args.sets.split(',') if s]
    sets = [s for s in C.ORDER if s in asked and (not s.startswith('S_PHR') or phr == 'PRESENT')]
    skipped_sets = [s for s in asked if s not in sets]
    sets = [s for s in sets if s not in ledger['dropped']]
    order = pop['track_order']
    decision = set(pop['decision']['captures'])
    if set(order) - set(entries):
        raise SystemExit(f'SEEDS.json lacks population captures {sorted(set(order) - set(entries))[:5]}')
    caps = order if args.captures == 'all' else [k for k in order if k in args.captures.split(',')]
    if args.captures != 'all' and len(caps) != len(args.captures.split(',')):
        raise SystemExit('--captures names captures outside the population')
    event('START', device=args.device, sets=sets, skipped=skipped_sets, dropped=ledger['dropped'], captures=len(caps),
          decision_captures=sum(k in decision for k in caps), spent_seconds=spent(), hard_stop=args.hard_stop, contract=spec,
          cuda_visible=os.environ.get('CUDA_VISIBLE_DEVICES'))

    import mc_tracker as MT
    import torch
    if args.device == 'cuda':
        if not torch.cuda.is_available():
            raise SystemExit('no CUDA device visible')
        if torch.cuda.get_device_capability(0) < (8, 0):
            event('REFUSED', reason='card without native bf16 (compute capability below 8.0)', device=torch.cuda.get_device_name(0))
            return 6
    tracker = MT.Sam3Carry(args.device)
    if args.device == 'cuda' and tracker.outside:
        event('REFUSED', reason='modules loaded from outside /scratch', modules=tracker.outside[:20])
        return 4
    base = dict(C.PINS)
    this_run = dict(started=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), host=os.uname().nodename, load_seconds=tracker.load_seconds,
                    device=torch.cuda.get_device_name(0) if args.device == 'cuda' else 'cpu',
                    card_bytes=torch.cuda.get_device_properties(0).total_memory if args.device == 'cuda' else None, units=0)
    ledger['runs'].append(this_run)
    import psutil
    proc = psutil.Process()
    slots_of = {k: capture_slots(frame_sets['captures'][k], entries[k], args.max_frames) for k in caps}
    masks_cache = {}

    def seed_masks(canonical):
        if canonical not in masks_cache:
            masks_cache.clear()
            masks_cache[canonical] = IO.load_seeds(canonical)
        return masks_cache[canonical]

    def expect(seed_set, fs, canonical):
        fsr = frame_sets['captures'][canonical]
        frames = plan_unit(seed_set, fs, fsr, entries[canonical], slots_of[canonical], False)[0]
        return dict(contract=spec, population_id=pop['population_id'],
                    frames_digest=digest([[d, fsr['dense'][d]['path'], fsr['dense'][d]['sha256']] for d in frames]),
                    seed_meta_digest=seed_meta_digest(seed_set, entries[canonical]),
                    seed_digest=seed_digest(seed_set, entries[canonical], seed_masks(canonical)))

    def done(s, canonical):
        """True when the unit's file exists under this binding; a file under another binding stops the pass."""
        p = IO.track_path(*s.split('/'), canonical, out)
        if not p.exists():
            return False
        have, want = C.read_json(p), expect(*s.split('/'), canonical)
        for key, value in want.items():
            if have.get(key) != value:
                raise SystemExit(f'{p}: {key} differs from this pass (incompatible resume); move the file aside')
        return True

    def predicted(s, canonical, rate):
        seed_set, fs = s.split('/')
        twin = seed_set == 'S_PHR' and (f'S_A0/{fs}' in sets or IO.track_path('S_A0', fs, canonical, out).exists())
        frames, _, track, _, _ = plan_unit(seed_set, fs, frame_sets['captures'][canonical], entries[canonical], slots_of[canonical], twin)
        return unit_cost(rate, len(frames), len(track))

    def remaining_by_set(rate):
        rem = {}
        for s, k in units(sets, caps):
            if not IO.track_path(*s.split('/'), k, out).exists():
                rem[s] = rem.get(s, 0.) + predicted(s, k, rate)
        return rem

    def reconsider(kind):
        """PROJECTION event (and the receipt the first time); drops trailing sets or stops. Returns False to stop."""
        nonlocal sets
        rate = rates(ledger)
        rem = remaining_by_set(rate)
        projection = project(spent(), rem, sets)
        drop = plan_drop(spent(), rem, sets, args.hard_stop)
        body = dict(stage=kind, rates=rate, remaining_seconds_by_set=rem, projected_seconds=projection,
                    projected_gpu_hours=projection/3600, spent_seconds=spent(), hard_stop_seconds=args.hard_stop, sets=sets, drop=drop)
        event('PROJECTION', **body)
        if kind == 'receipt':
            timing_receipt(out, dict(body, device=this_run['device'], host=this_run['host'], load_seconds=this_run['load_seconds'],
                                     card_bytes=this_run['card_bytes'], a0_d64_captures_measured=ledger['a0_d64_units'],
                                     embed_note='each arm embeds the frames it reads once per capture; remaining seconds count it',
                                     decision='stop: S_A0/D64 alone exceeds the hard stop' if drop is None else
                                     f'continue; drop {drop}' if drop else 'continue with every set'))
            ledger['receipt'] = str(out/'TIMING_RECEIPT.json')
        if drop is None:
            ledger['stopped'] = f'PROJECTION: {sets[0]} alone exceeds {args.hard_stop} s'
            return False
        if drop:
            ledger['dropped'] += drop
            sets = [s for s in sets if s not in drop]
        return True

    worked = since = 0
    for s, canonical in units(sets, caps):
        if s not in sets:
            continue
        if done(s, canonical):
            continue
        seed_set, fs = s.split('/')
        rate = rates(ledger)
        if spent() + predicted(s, canonical, rate) > args.hard_stop:
            ledger['stopped'] = f'HARD_STOP before {s} {canonical}'
            break
        u0 = time.monotonic()
        C.PINS.clear(); C.PINS.update(base)
        fsr, entry = frame_sets['captures'][canonical], entries[canonical]
        C.PINS[str(C.OUT/'seeds'/(C.stub(canonical)+'.npz'))] = entry['seeds_sha256']
        masks = seed_masks(canonical)
        twin_path = IO.track_path('S_A0', fs, canonical, out)
        twin = {r['k']: r for r in C.read_json(twin_path)['objects']} if seed_set == 'S_PHR' and twin_path.exists() else {}
        frames, anchor_pos, track, reuse, skipped_objects = plan_unit(seed_set, fs, fsr, entry, slots_of[canonical], bool(twin))
        embed_s, hw, track_s = 0., None, 0.
        objects = [dict(twin[o['k']], reused_from='S_A0', seconds=0.) for o in reuse]
        if track:
            images = tracker.frames([fsr['dense'][d]['path'] for d in frames], [fsr['dense'][d]['sha256'] for d in frames])
            for d in frames:
                C.PINS[fsr['dense'][d]['path']] = fsr['dense'][d]['sha256']
            e0 = time.monotonic()
            cache, hw = tracker.embed(images)
            embed_s = time.monotonic() - e0
            del images
            for o in track:
                seed = o[seed_set]
                mask = masks[f"{seed_set}_{o['k']}"]
                o0 = time.monotonic()
                result = tracker.track(cache, anchor_pos[seed['slot']-1], mask)
                rec = IO.object_record(o['k'], o['name'], o['instance'], seed['slot'], frames, anchor_pos, result, mask)
                rec['seconds'] = time.monotonic() - o0
                track_s += rec['seconds']
                objects.append(rec)
                if proc.memory_info().rss > args.rss_limit_gib*2**30:
                    raise MemoryError(f'RSS above {args.rss_limit_gib} GiB')
            del cache
        objects.sort(key=lambda r: r['k'])
        unit_s = time.monotonic() - u0
        C.write_json(IO.track_path(seed_set, fs, canonical, out),
                     dict(expect(seed_set, fs, canonical), capture=canonical, seed_set=seed_set, frame_set=fs, tracker='sam3_video_tracker',
                          status='OK', decision_population=canonical in decision, dense_slots=frames, embedded_frames=len(frames) if track else 0,
                          embed_seconds=embed_s, track_seconds=track_s, seconds=unit_s, objects=objects, skipped_objects=skipped_objects,
                          partial=bool(args.max_frames), native_hw=list(hw) if hw else None,
                          cuda_peak_gib=torch.cuda.max_memory_allocated()/2**30 if args.device == 'cuda' else None,
                          cuda_reserved_peak_gib=torch.cuda.max_memory_reserved()/2**30 if args.device == 'cuda' else None,
                          rss_gib=proc.memory_info().rss/2**30,
                          peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20), gz=True)
        r = ledger['rates']
        r['units'] += 1; r['unit_seconds'] += unit_s; r['embed_seconds'] += embed_s; r['track_seconds'] += track_s
        r['embed_frames'] += len(frames) if track else 0; r['object_frames'] += len(track)*len(frames)
        worked += 1
        this_run['units'] = worked
        if s == 'S_A0/D64':
            ledger['a0_d64_units'] += 1
        ledger['spent_seconds'] = spent()
        save_ledger(out, ledger)
        event('UNIT', set=s, capture=canonical, decision_population=canonical in decision, embedded_frames=len(frames) if track else 0,
              tracked=len(track), reused=len(reuse), embed_seconds=embed_s, track_seconds=track_s, seconds=unit_s,
              spent_seconds=ledger['spent_seconds'])
        if ledger['receipt'] is None:
            if ledger['a0_d64_units'] >= args.project_after and not reconsider('receipt'):
                break
            continue
        since += 1
        if since >= 10:
            since = 0
            if not reconsider('periodic'):
                break
    C.PINS.clear(); C.PINS.update(base); C.code_pins()
    count = {s: sum(IO.track_path(*s.split('/'), k, out).exists() for k in caps) for s in C.ORDER}
    count_decision = {s: sum(IO.track_path(*s.split('/'), k, out).exists() for k in caps if k in decision) for s in C.ORDER}
    C.write_json(out/'TRACK_INDEX.json', dict(sets_run=sets, dropped=ledger['dropped'], skipped=skipped_sets, stopped=ledger['stopped'],
                                              captures=len(caps), population_id=pop['population_id'], done=count,
                                              done_decision=count_decision, spent_seconds=spent(), contract=spec, rates=rates(ledger)))
    event('END', stopped=ledger['stopped'], done=count, done_decision=count_decision, spent_seconds=spent(),
          seconds=time.monotonic()-t_start)
    return 0 if not ledger['stopped'] else 2


if __name__ == '__main__':
    sys.exit(main())
