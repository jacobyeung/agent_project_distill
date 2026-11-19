"""Collate the CPU dry run into out/v2/DRYRUN.json (each step's verdict, with the sha256 of the file it reads), the
full-capture CPU check (step 4), the GPU-hour estimate and the GPU memory need.
GPU hours: the pass's own plan_unit over SEEDS.json and FRAME_SETS.json gives every (arm, capture) unit's embedded frames
and tracked objects; each arm embeds the frames it reads once per capture (D64 dense, A32 anchors), and an S_PHR seed equal
to its S_A0 seed reuses the S_A0 record. Rates are assumed until the 10-capture TIMING_RECEIPT.json replaces them.
Usage: python mc_dryrun_report.py   (p1cpu interpreter)
"""
import json
import mc_common as C
import mc_track_pass as TP

# Assumed GPU rates (bf16 on an Ampere/Ada card): SAM 3's ViT backbone at 1008 px is about 4.7 TFLOP per frame, about
# 0.12 s at 40 TFLOP/s sustained; one tracker step (memory attention, mask decoder, memory encoder, Python) about 25 ms
# per object-frame; 60 s to load. The 10-capture TIMING_RECEIPT.json replaces all three.
EMBED_S, TRACK_S, LOAD_S = .12, .025, 60.
HARD_STOP_H = 2.0
FULL = 'arkitscenes/41048124'
# GPU memory (bytes), batch 1 frame per backbone forward and 1 object per tracker step: fp32 weights (the checkpoint), the
# per-frame cache the pass keeps for every frame of a unit (fp32 1008 px image, bf16 backbone levels 32ch@288^2, 64ch@144^2,
# 256ch@72^2), the bf16 ViT forward's activation peak at 1008 px (windowed attention) and the CUDA context.
FRAME_CACHE = 3*1008*1008*4 + 2*(32*288*288 + 64*144*144 + 256*72*72)
ACTIVATIONS, CONTEXT = 1.5e9, 1.0e9
CARD_MIN = 24e9


def estimate(frame_sets, entries, caps, sets):
    per = {}
    for s in sets:
        seed_set, fs = s.split('/')
        u = dict(units=0, embed_frames=0, object_frames=0, objects=0, reused=0)
        for k in caps:
            frames, _, track, reuse, _ = TP.plan_unit(seed_set, fs, frame_sets['captures'][k], entries[k],
                                                      TP.capture_slots(frame_sets['captures'][k], entries[k], 0), True)
            u['reused'] += len(reuse)
            if track:
                u['units'] += 1; u['embed_frames'] += len(frames); u['objects'] += len(track); u['object_frames'] += len(track)*len(frames)
        u['hours'] = (u['embed_frames']*EMBED_S + u['object_frames']*TRACK_S)/3600
        per[s] = u
    cum, rows, keep = LOAD_S/3600, [], []
    for s in sets:
        cum += per[s]['hours']
        rows.append(dict(set=s, hours=per[s]['hours'], cumulative_hours=cum, fits_hard_stop=cum <= HARD_STOP_H))
        if cum <= HARD_STOP_H:
            keep.append(s)
    return dict(per_set=per, cumulative=rows, total_hours=cum, decision_arm_hours=LOAD_S/3600+per[sets[0]]['hours'],
                kept_at_assumed_rates=keep, dropped_at_assumed_rates=[s for s in sets if s not in keep],
                old_single_embedding_estimate_hours=1.48253,
                rates=dict(embed_seconds_per_frame=EMBED_S, track_seconds_per_object_frame=TRACK_S, load_seconds=LOAD_S),
                binding='TIMING_RECEIPT.json after the first 10 S_A0/D64 captures replaces these rates; the pass drops trailing '
                        'sets while its projection exceeds the 2 h cumulative stop')


def memory(max_frames):
    weights = C.CHECKPOINT_BYTES
    cache = FRAME_CACHE*max_frames
    total = weights + cache + ACTIVATIONS + CONTEXT
    return dict(weights_fp32=weights, frame_cache_per_frame=FRAME_CACHE, frames_per_unit=max_frames, frame_cache=cache,
                activations=ACTIVATIONS, cuda_context=CONTEXT, total_bytes=total, card_min_bytes=CARD_MIN,
                margin=CARD_MIN/total, fits_24GB=total*2 <= CARD_MIN, bf16='native bf16 needs compute capability >= 8.0 (Ampere or later)',
                batch='one frame per backbone forward; one object per tracker step; a unit holds at most 64 frames')


def full_capture(o):
    d = o/'dry/track_cpu_full'
    events = [json.loads(l) for l in (d/'EVENTS.jsonl').read_text().splitlines()]
    start = [e for e in events if e['event'] == 'START'][-1]
    end = next((e for e in reversed(events) if e['event'] == 'END'), None)
    units = [e for e in events if e['event'] == 'UNIT']
    proj = [e for e in events if e['event'] == 'PROJECTION']
    index = C.read_json(d/'TRACK_INDEX.json') if (d/'TRACK_INDEX.json').exists() else {}
    ledger = C.read_json(d/'BUDGET.json')
    done = (end or {}).get('done', {})
    complete = bool(end) and not ledger.get('stopped') and all(done.get(s) == 1 for s in start['sets'])
    by = {u['set']: dict(embedded_frames=u['embedded_frames'], tracked=u['tracked'], reused=u['reused'], embed_seconds=u['embed_seconds'],
                         track_seconds=u['track_seconds'], seconds=u['seconds']) for u in units}
    peak = max((C.read_json(p).get('peak_rss_gib', 0.) for p in d.glob('*/*.json.gz')), default=None)
    priced = sorted(p.name for p in (o/'dry/price_cpu_full').iterdir() if (p/'PRICE_INDEX.json').exists()) if (o/'dry/price_cpu_full').exists() else []
    return dict(capture=FULL, status='COMPLETE' if complete else 'PARTIAL', threads=8, limit_seconds=2700, spent_seconds=ledger['spent_seconds'],
                wall_seconds=(end or {}).get('seconds'), sets=start['sets'], done=done, stopped=ledger.get('stopped'), dropped=ledger.get('dropped'),
                units=by, rates=index.get('rates'), projections=[{k: p.get(k) for k in ('stage', 'projected_seconds', 'drop')} for p in proj],
                projected_all_sets_seconds=proj[0]['projected_seconds'] if proj else None,
                peak_rss_gib=peak, priced=priced)


def main():
    C.scoring_guard(C.OUT)
    o = C.OUT
    j = lambda p: C.read_json(o/p)
    step0 = j('dry/STEP0_PRECISION.json')['summary']
    stub = j('dry/STUB_PARITY.json')
    frames_raw = j('FRAME_SETS.json')
    seeds = j('seeds/SEEDS.json')
    seeds5 = j('seeds/SEEDS_first5.json')
    guard = j('GUARD.json')
    pred = j('dry/PREDICTOR_CPU.json')
    staging = j('STAGING.json')
    pop = C.population()
    tests = (C.WORK/'logs/tests.log').read_text().strip().splitlines()[-1]
    entries = {r['capture']: r for r in seeds['captures']}
    sets = [s for s in C.ORDER if not s.startswith('S_PHR') or seeds['summary']['S_PHR']['status'] == 'PRESENT']
    gpu = estimate(C.frame_sets(), entries, pop['track_order'], sets)
    ck = stub['checks']
    out = dict(
        step0=dict(passed=step0['reproduced'], tau_025=step0['tau_025'], predicate_equal=f"{step0['predicate_equal']}/{step0['object_taus']}"),
        step1=dict(all_1037=ck['step1_seed_stub_C_best1_vs_A0_deployed'], decision_1012=ck['step1_seed_stub_C_best1_vs_A0_deployed_decision']),
        step1b=dict(empty_stub_C_best1=ck['step1b_empty_stub_C_best1_vs_A0_deployed'], empty_members=ck['step1b_empty_members_in_denominator']),
        step2=dict(C_best1_vs_A2=ck['step2_raster_stub_C_best1_vs_A2_gt_masks'], C_fused_vs_fused_cf=ck['step2_raster_stub_C_fused_vs_fused_cf'],
                   decision_1012={k: ck[k+'_decision']['passed'] for k in ('step2_raster_stub_C_best1_vs_A2_gt_masks', 'step2_raster_stub_C_fused_vs_fused_cf')}),
        step3=dict(status=frames_raw['status'], captures=len(frames_raw['captures']), frames=sum(len(c['dense']) for c in frames_raw['captures']),
                   failures=len(frames_raw['failures'])),
        step4a=dict(status=pred['status'], attempts=[{k: a.get(k) for k in ('label', 'status', 'error', 'raised_at')} for a in pred['attempts']]),
        step4=full_capture(o),
        seeds=dict(check1_first5=seeds5['check1'], check1_all=seeds['check1'], summary=seeds['summary']),
        population=dict(population_id=pop['population_id'], **pop['counts']),
        guard=dict(exclusions={k: dict(passed=v['passed'], hits=len(v['hit_captures']), rows=v['hit_rows']) for k, v in guard['lists'].items()},
                   withheld_default=guard['withheld_default'], k1_split=guard['k1_split']['passed'], folds=guard['folds']['passed'],
                   reuse_K1_TRACK=guard['reuse_K1_TRACK']['status']),
        deployed_frame_recall=stub['deployed_reference']['beside/all']['frame_recall'],
        frame_spacing=stub['frame_spacing'],
        tests=tests, staging=dict(total_bytes=staging['total_bytes'], items=len(staging['items'])),
        gpu_estimate=gpu, gpu_memory=memory(64))
    C.code_pins()
    C.write_json(o/'DRYRUN.json', out)
    print(json.dumps(dict(gpu_estimate={k: gpu[k] for k in ('total_hours', 'decision_arm_hours', 'kept_at_assumed_rates')},
                          step4={k: out['step4'][k] for k in ('status', 'spent_seconds', 'done')}, memory=out['gpu_memory']['total_bytes'],
                          tests=tests), default=str))
    C.status(f"Dry-run collation (DRYRUN.json): step 4 {out['step4']['status']} in {out['step4']['spent_seconds']:.0f} s; tests {tests}; "
             f"GPU estimate {gpu['total_hours']:.2f} h with per-arm embedding (decision arm {gpu['decision_arm_hours']:.2f} h; "
             f"drops {gpu['dropped_at_assumed_rates']} at assumed rates), hard stop 2.0 h; memory {out['gpu_memory']['total_bytes']/1e9:.1f} GB.")


if __name__ == '__main__':
    main()
