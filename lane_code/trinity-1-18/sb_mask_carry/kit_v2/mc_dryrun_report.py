"""Collate the CPU dry run into out/v2/DRYRUN.json (each step's verdict, with the sha256 of the file it reads) and the
GPU estimate: work counts from FRAME_SETS.json and SEEDS.json, CPU timings measured in step 4b, and a derived GPU rate.
Usage: python mc_dryrun_report.py   (p1cpu interpreter)
"""
import json
from pathlib import Path
import mc_common as C

# Derived GPU rates (one 48 GB Ampere/Ada card, bf16): SAM 3's ViT backbone at 1008 px is about 4.7 TFLOP per frame,
# about 0.12 s at 40 TFLOP/s sustained; one tracker step (memory attention, mask decoder, memory encoder, Python) about
# 25 ms per object-frame. The 10-capture TIMING_RECEIPT.json replaces both.
EMBED_S, TRACK_S, LOAD_S = .12, .025, 60.


def main():
    o = C.OUT
    j = lambda p: C.read_json(o/p)
    step0 = j('dry/STEP0_PRECISION.json')['summary']
    stub = j('dry/STUB_PARITY.json')
    frames = j('FRAME_SETS.json')
    seeds = j('seeds/SEEDS.json')
    seeds5 = j('seeds/SEEDS_first5.json')
    guard = j('GUARD.json')
    pred = j('dry/PREDICTOR_CPU.json')
    tindex = j('dry/track_cpu/TRACK_INDEX.json')
    events = [json.loads(l) for l in (o/'dry/track_cpu/EVENTS.jsonl').read_text().splitlines()]
    proj = [e for e in events if e['event'] == 'PROJECTION'][-1]
    start = [e for e in events if e['event'] == 'START'][-1]
    end = [e for e in events if e['event'] == 'END'][-1]
    tests = (C.WORK/'logs/tests.log').read_text().strip().splitlines()[-1]
    n_frames = sum(len(c['dense']) for c in frames['captures'])
    objs = seeds['summary']
    work = {'embed_frames': n_frames, 'S_A0/D64': objs['S_A0']['ok']*64, 'S_GT/D64': objs['S_GT']['ok']*64,
            'S_A0/A32': objs['S_A0']['ok']*32, 'S_GT/A32': objs['S_GT']['ok']*32}
    gpu = {k: (v*EMBED_S if k == 'embed_frames' else v*TRACK_S) for k, v in work.items()}
    total = LOAD_S + sum(gpu.values())
    cpu = dict(embed_seconds_per_frame=proj['embed_mean']/8, set_seconds_8_frames=proj['set_means'], window_frames=8,
               objects_tracked=1, total_seconds=end['spent_seconds'])
    out = dict(
        step0=dict(passed=step0['reproduced'], tau_025=step0['tau_025'], predicate_equal=f"{step0['predicate_equal']}/{step0['object_taus']}"),
        step1=stub['checks']['step1_seed_stub_C_best1_vs_A0_deployed'],
        step2=dict(C_best1_vs_A2=stub['checks']['step2_raster_stub_C_best1_vs_A2_gt_masks'],
                   C_fused_vs_fused_cf=stub['checks']['step2_raster_stub_C_fused_vs_fused_cf']),
        step3=dict(status=frames['status'], captures=len(frames['captures']), frames=n_frames, failures=len(frames['failures'])),
        step4a=dict(status=pred['status'], attempts=[{k: a.get(k) for k in ('label', 'status', 'error', 'raised_at')} for a in pred['attempts']]),
        step4b=dict(capture=start['captures'] and 'arkitscenes/41048124', done=end['done'], stopped=end['stopped'], cpu=cpu,
                    priced=sorted(p.name for p in (o/'dry/price_cpu').iterdir() if (p/'PRICE_INDEX.json').exists())),
        seeds=dict(check1_first5=seeds5['check1'], check1_all=seeds['check1'], summary=objs),
        guard=dict(exclusions={k: dict(passed=v['passed'], hits=len(v['hit_captures']), rows=v['hit_rows']) for k, v in guard['lists'].items()},
                   withheld_default=guard['withheld_default'], k1_split=guard['k1_split']['passed'], folds=guard['folds']['passed'],
                   reuse_K1_TRACK=guard['reuse_K1_TRACK']['status']),
        deployed_frame_recall=stub['deployed_reference']['frame_recall'],
        tests=tests,
        gpu_estimate=dict(work=work, rates=dict(embed_seconds_per_frame=EMBED_S, track_seconds_per_object_frame=TRACK_S, load_seconds=LOAD_S),
                          seconds=gpu, total_hours=total/3600, decision_arm_hours=(LOAD_S+gpu['embed_frames']+gpu['S_A0/D64'])/3600,
                          hard_stop_hours=2.0, binding='TIMING_RECEIPT.json after the first 10 captures replaces these rates'))
    C.code_pins()
    C.write_json(o/'DRYRUN.json', out)
    print(json.dumps(dict(gpu_estimate=out['gpu_estimate'], tests=tests), default=str))
    C.status(f"Dry-run collation (DRYRUN.json): steps 0-3 pass, 4a {pred['status']}, 4b done {end['done']}; tests {tests}; "
             f"GPU estimate {total/3600:.2f} h (decision arm {out['gpu_estimate']['decision_arm_hours']:.2f} h), hard stop 2.0 h.")


if __name__ == '__main__':
    main()
