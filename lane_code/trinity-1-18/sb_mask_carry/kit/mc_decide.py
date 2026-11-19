"""Measures, bars and decision on priced carried tracks (the bars as written in KIT_SPEC_mask_carry.md).

Arms per complete (seed set, frame set): C_best1, C_fused. The bar seed set is S_PHR when PHRASE_SET.json is frozen,
else S_A0. The frame set is cross-fit: for each of the ladder's five room folds, the frame set with the higher C_fused
MRA on the other four folds (ties D64) serves that fold's rows.
  carry_precision    member precision (carried anchors other than the seed, IoU > 0.5, predicted.member_precision)
                     on on-target seeds (seed IoU >= 0.5) >= 90%
  carry_fusion       C_fused - A0_deployed >= +2.0 points, room-bootstrap 95% lower bound > 0
  size_screen        sizes(C_fused) vs sizes(A0): estimate >= 5 and lower bound > 0 (box ladder v2, unchanged)
  first_seen_screen  appearance(C_fused) pair rate >= 0.90 (box ladder v2, unchanged)
  carry_ceiling      diagnostic: S_GT C_fused against fused_cf 78.62; S_GT frame recall
Usage: python mc_decide.py [price_root] [out_dir]   (p1cpu interpreter; defaults out/price, out/)
"""
import json, sys, time
from pathlib import Path
import numpy as np
import mc_common as C
import mc_ladder as L
import mc_measure as MS

BAR = dict(precision=.90, fusion=2.0, size=5.0, first_seen=.90)


def ST():
    L.T()
    import summarize_train
    return summarize_train


def load_arm(path):
    files = sorted(Path(path).glob('*.json.gz'))
    data = [C.read_json(p) for p in files]
    complete = len(data) == 209 and all(d['track_status'] == 'OK' for d in data)
    return dict(items=[r for d in data for r in d['items']], table=[r for d in data for r in d['table']],
                records=[r for d in data for r in d['records']], complete=complete, captures=len(data),
                missing_tracks=sum(d['track_status'] == 'MISSING' for d in data))


def member_precision(rows, subset):
    obs = [o for o in ST().objects(rows) if o.get('carry_status') == 'OK' and subset(o)]
    n = sum(o['member_precision']['members'] for o in obs)
    hit = sum(o['member_precision']['correct'] for o in obs)
    maj = sum(o['majority_correct'] for o in obs)
    return dict(objects=len(obs), members=n, correct=hit, precision=hit/n if n else None,
                seed_majority_correct=maj, seed_majority_precision=maj/n if n else None)


def mask_iou(records):
    mf = MS.maskfail()
    s = mf.stats(records)
    return dict(stats=s, frame_recall=MS.frame_recall(records), frame_recall_unique=MS.frame_recall(MS.unique(records)),
                false_presence=MS.false_presence(records), false_presence_unique=MS.false_presence(MS.unique(records)))


def arm_measures(arm, a0):
    t = ST()
    best1 = [r for r in arm['items'] if r['arm'].startswith('C_best1/')]
    fused = [r for r in arm['items'] if r['arm'].startswith('C_fused/')]
    return dict(rows=len(fused), C_best1=t.mean(best1), C_fused=t.mean(fused),
                refusals=sum(r['prediction'] is None for r in fused),
                C_best1_vs_A0=t.contrast(best1, a0), C_fused_vs_A0=t.contrast(fused, a0),
                precision_on_target=member_precision(fused, lambda o: o['on_target']),
                precision_all=member_precision(fused, lambda o: True),
                first_seen=t.appearance(fused), size=t.contrast(t.sizes(fused), t.sizes(a0)), size_mra=t.mean(t.sizes(fused)),
                masks=mask_iou(arm['records']))


def crossfit(arms, seed_set):
    """Per fold k, the frame set whose C_fused MRA on folds != k is higher (ties D64); fold k's rows come from it."""
    t = ST()
    have = sorted({fs for s, fs in arms if s == seed_set}, key=lambda fs: (fs not in C.FRAME_SETS, C.FRAME_SETS.index(fs) if fs in C.FRAME_SETS else fs))
    choice, rows = {}, []
    for k in range(5):
        scores = {fs: t.mean([r for r in arms[(seed_set, fs)]['items'] if r['arm'].startswith('C_fused/') and r['fold'] != k]) for fs in have}
        pick = max(have, key=lambda fs: (scores[fs], fs == 'D64'))
        choice[str(k)] = dict(frame_set=pick, fit_mra=scores)
        rows += [dict(r, arm=f'C_fused_cf/{seed_set}', chosen=r['arm']) for r in arms[(seed_set, pick)]['items']
                 if r['arm'].startswith('C_fused/') and r['fold'] == k]
    return rows, choice


def bars(cf_rows, a0, gt_rows):
    t = ST()
    prec = member_precision(cf_rows, lambda o: o['on_target'])
    gain = t.contrast(cf_rows, a0)
    size = t.contrast(t.sizes(cf_rows), t.sizes(a0))
    first = t.appearance(cf_rows)
    out = dict(
        carry_precision=dict(value=prec['precision'], members=prec['members'], correct=prec['correct'], bar='>= 0.90',
                             passed=prec['precision'] is not None and prec['precision'] >= BAR['precision']),
        carry_fusion=dict(estimate=gain['estimate'], ci95=gain['ci95'], left_mra=gain['left_mra'], right_mra=gain['right_mra'],
                          bar='>= +2.0 and ci95[0] > 0', passed=gain['estimate'] >= BAR['fusion'] and gain['ci95'][0] > 0),
        size_screen=dict(estimate=size['estimate'], ci95=size['ci95'], left_mra=size['left_mra'], right_mra=size['right_mra'],
                         objects=size['rows'], bar='>= +5 and ci95[0] > 0', passed=size['estimate'] >= BAR['size'] and size['ci95'][0] > 0),
        first_seen_screen=dict(rate=first['rate'], pairs=first['pairs'], correct=first['correct'], bar='>= 0.90',
                               passed=first['rate'] is not None and first['rate'] >= BAR['first_seen']))
    if gt_rows is not None:
        out['carry_ceiling'] = dict(S_GT_C_fused=t.mean(gt_rows), fused_cf=78.62102217936354, role='diagnostic')
    return out


def decision(b):
    if not b['carry_precision']['passed']:
        return dict(route='OBJECT_ARMS_CLOSED', joins_stack=False,
                    text='carry_precision fails: the object arms (size, appearance order, counting) stay closed.', opens=[])
    opens = [x for x, k in (('size R0-dev comparison', 'size_screen'), ('appearance-order R0-dev comparison', 'first_seen_screen')) if b[k]['passed']]
    if b['carry_fusion']['passed']:
        return dict(route='JOIN_STACK', joins_stack=True, opens=opens,
                    text='carry_precision and carry_fusion pass: the carried, fused track joins the stack.')
    return dict(route='NO_JOIN', joins_stack=False, opens=opens,
                text='carry_precision passes and carry_fusion fails: the carried track does not join the stack.')


def fmt(x, pct=False):
    if x is None:
        return 'n/a'
    return f'{100*x:.1f}%' if pct else f'{x:.2f}'


def report(out, m, b, dec, cf_choice, bar_set, status, label):
    lines = [f'# Mask carry: {label}', '',
             f'Bars read on {bar_set} (S_PHR: {status["S_PHR"]}); frame set cross-fit by room fold. Decision: **{dec["route"]}**. {dec["text"]}', '',
             '| Seed set | Frame set | C_best1 | C_fused | C_fused - A0 [95%] | Precision on-target | Size - A0 [95%] | First-seen | Frame recall |',
             '|---|---|---|---|---|---|---|---|---|']
    for (s, fs), v in m.items():
        g = v['C_fused_vs_A0']; sz = v['size']; p = v['precision_on_target']
        lines.append(f"| {s} | {fs} | {v['C_best1']:.2f} | {v['C_fused']:.2f} | {g['estimate']:+.2f} [{g['ci95'][0]:+.2f}, {g['ci95'][1]:+.2f}] | "
                     f"{fmt(p['precision'], True)} ({p['correct']}/{p['members']}) | {sz['estimate']:+.2f} [{sz['ci95'][0]:+.2f}, {sz['ci95'][1]:+.2f}] | "
                     f"{fmt(v['first_seen']['rate'], True)} | {fmt(v['masks']['frame_recall']['rate'], True)} |")
    lines.append(f"| {bar_set} | cross-fit | | {b['carry_fusion']['left_mra']:.2f} | {b['carry_fusion']['estimate']:+.2f} "
                 f"[{b['carry_fusion']['ci95'][0]:+.2f}, {b['carry_fusion']['ci95'][1]:+.2f}] {'PASS' if b['carry_fusion']['passed'] else 'FAIL'} | "
                 f"{fmt(b['carry_precision']['value'], True)} {'PASS' if b['carry_precision']['passed'] else 'FAIL'} | "
                 f"{b['size_screen']['estimate']:+.2f} {'PASS' if b['size_screen']['passed'] else 'FAIL'} | "
                 f"{fmt(b['first_seen_screen']['rate'], True)} {'PASS' if b['first_seen_screen']['passed'] else 'FAIL'} | |")
    lines += ['', 'A0_deployed 56.77 (36 refusals scored 0); A2_gt_masks 73.97; fused_cf 78.62. Deployed frame recall 57.9%, best pool candidate 74.8%, '
              'false presence 976 operand-frames, first-seen pairs 76.56%, size MRA 52.36 on 770 objects.',
              'Frame-set choice per fold: ' + ', '.join(f"{k}: {v['frame_set']}" for k, v in cf_choice.items()) + '.', '']
    for (s, fs), v in m.items():
        mk = v['masks']
        lines.append(f"- {s}/{fs}: all-seed precision {fmt(v['precision_all']['precision'], True)} "
                     f"({v['precision_all']['correct']}/{v['precision_all']['members']}), seed-majority {fmt(v['precision_on_target']['seed_majority_precision'], True)}; "
                     f"false presence {mk['false_presence']['with_mask']} operand-frames; refusals {v['refusals']}.")
    if 'carry_ceiling' in b:
        lines.append(f"- carry_ceiling (diagnostic): S_GT C_fused {b['carry_ceiling']['S_GT_C_fused']:.2f} against fused_cf 78.62.")
    lines += ['', 'Held-out captures, R0-dev, dev-S1 and official items were not opened; every number is on the 1,037 K1 training rows.']
    (out/'CARRY_REPORT.md').write_text('\n'.join(lines)+'\n')


def main():
    t0 = time.monotonic()
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else C.OUT/'price'
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else C.OUT
    label = 'DRY RUN ON STUB TRACKERS (not a result)' if 'dry' in str(root) else 'K1 training, SAM 3 tracker'
    seeds = C.read_json(C.OUT/'seeds/SEEDS.json')
    phr = seeds['summary']['S_PHR']['status']
    arms = {}
    for d in sorted(root.iterdir()):
        if d.is_dir() and d.name.count('_') == 2:
            s, fs = '_'.join(d.name.split('_')[:2]), d.name.split('_')[2]
            arm = load_arm(d)
            if arm['complete']:
                arms[(s, fs)] = arm
    a0 = [r for (arm, _), r in L.published(('A0_deployed',)).items()]
    measures = {k: arm_measures(v, a0) for k, v in sorted(arms.items(), key=lambda kv: (kv[0][1] != 'D64', kv[0][0]))}
    wanted = 'S_PHR' if phr == 'PRESENT' else 'S_A0'
    bar_set = next((s for s in (wanted, 'S_A0') if any(k[0] == s for k in arms)), None)
    if bar_set is None:
        raise SystemExit('no complete S_PHR or S_A0 arm under '+str(root)+'; S_GT is a ceiling and never carries the bars')
    cf_rows, cf_choice = crossfit(arms, bar_set)
    gt_rows = crossfit(arms, 'S_GT')[0] if any(k[0] == 'S_GT' for k in arms) else None
    b = bars(cf_rows, a0, gt_rows)
    if gt_rows is not None:
        b['carry_ceiling']['S_GT_frame_recall'] = {fs: measures[('S_GT', fs)]['masks']['frame_recall'] for s, fs in arms if s == 'S_GT'}
    dec = decision(b)
    C.PINS.clear()
    for d in sorted(root.iterdir()):
        if (d/'PRICE_INDEX.json').exists():
            C.pin(d/'PRICE_INDEX.json')
    C.pin(C.OUT/'seeds/SEEDS.json'); C.code_pins()
    status = dict(S_PHR=phr, bars_wanted_on=wanted, bars_read_on=bar_set, arms=[f'{s}/{fs}' for s, fs in arms], label=label)
    C.write_json(out/'CARRY_DECISION.json', dict(label=label, bar_seed_set=bar_set, frame_set_choice=cf_choice, bars=b, decision=dec,
                                                 status=status, measures={f'{s}/{fs}': v for (s, fs), v in measures.items()}))
    with open(out/'PER_ITEM.jsonl', 'w') as f:
        for (s, fs), arm in arms.items():
            for r in arm['items']:
                f.write(json.dumps(C.clean(r))+'\n')
        for r in cf_rows:
            f.write(json.dumps(C.clean(r))+'\n')
    C.write_json(out/'K1_CARRY.json', dict(fields='per object and anchor: seed, carried flag, IoU at 240x320, raster share (native)',
                                           arms={f'{s}/{fs}': arm['table'] for (s, fs), arm in arms.items()}))
    report(out, measures, b, dec, cf_choice, bar_set, status, label)
    print(json.dumps(dict(decision=dec['route'], bars={k: v.get('passed') for k, v in b.items()}, seconds=time.monotonic()-t0)))


if __name__ == '__main__':
    main()
