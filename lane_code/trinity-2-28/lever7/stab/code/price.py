"""STAB pricing (DESIGN_STAB.md, Arms / Items / Reading and bars). Refuses to run without stab/REVIEW_GO.

Per type, per arm (own = own heads 170631/170706, decline = direct read 169526): an item on a capture whose K5
disagreement exceeds tau (TAU.json) takes the arm's banked answer; every other item keeps the baseline's (171253).
Item score: score_nfa.item_score (0 for a capped read, else output.scores.answer) for 171253 and own rows; the
direct read's compact score, zeroed on a forced close, token cap, error finish or parse failure (capped_zeroed).
Difference swap - baseline in points over all 150 items (unflagged items differ by 0); paired room bootstrap
(resample room_key with replacement, ratio of sums, 10,000 draws, seed 20261115, h1eval.statistics draw order);
Bonferroni 99.375% two-sided interval (2 arms x 4 types); 95% two-sided interval.
Decidable type: >= 10 flagged items in >= 3 rooms and ceiling 100 x flagged / 150 >= 2 points.
Lane ruling (F1, before any score): a decidable type with fewer than 6 flagged rooms is labelled "can close, cannot
pass" (a bootstrap draw with no flagged room gives exactly 0, so its 0.3125th percentile cannot exceed 0); it may close
but never pass. A pass needs >= 6 flagged rooms plus the decidable rule.
Worth building: some type that can pass and arm with difference >= +1.0 and 99.375% lower bound > 0.
Closed: on every decidable type both arms' 95% upper bounds < +1.0. Too few: no decidable type. Else undecided.
Conservative choices (not fixed by the design): distance passes only if it passes against both 171253 distance
reads (read 1, the pinned candidates_argmax baseline; read 0 null_argmax, which holds the registered 26.93 and
matches the own arm's selector) and closes only
if it closes against both; a decline-arm pass counts as undecided while the direct read's anchor frames are unchecked.
Oracle: best of the three arms per flagged item (ceiling, reported only). Fragile-flag sensitivity: flags of captures
with tau/2 <= disagreement <= 2 tau flipped, everything repriced and the reading reported beside.
"""
import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script directory
import common as C  # noqa: E402

DRAWS = 10000
SEED = 20261115
BLOCK = 200
LEVEL_BONF = 1 - 0.05/8          # 99.375%
BAR = 1.0
MIN_ITEMS, MIN_ROOMS, MIN_CEIL = 10, 3, 2.0
MIN_PASS_ROOMS = 6               # F1 lane ruling
OWN_CAMERA_CAVEAT = ('Caveat: the own-heads camera answers come from job 170631, whose head outputs (pose9) differ from '
                     '171253\'s on all 450 camera items (median max-abs difference 0.017, max 0.19; DRYCHECK.json); '
                     'own-heads distance (170706) agrees bit for bit on 150/150.')
ARMS = ('own', 'direct')
ARM_NAME = {'own': '(ii) own heads', 'direct': '(i) decline the call', 'base': '(iii) baseline tower'}


class Refused(RuntimeError):
    pass


def guard(stab=C.STAB):
    go = Path(stab)/'REVIEW_GO'
    if not go.is_file():
        raise Refused('refused: %s does not exist; pricing waits for the review' % go)
    return go


def bootstrap(values, draws=DRAWS, seed=SEED):
    """values: (room, value). h1eval.statistics.bootstrap's estimator and draw order, returning the samples too."""
    groups = defaultdict(list)
    for room, v in values:
        if v is None or not math.isfinite(float(v)):
            raise ValueError('non-finite item value')
        groups[room].append(float(v))
    groups = [groups[k] for k in sorted(groups)]
    sums = np.array([sum(v) for v in groups])
    counts = np.array([len(v) for v in groups])
    rng = np.random.default_rng(seed)
    samples = []
    for start in range(0, draws, BLOCK):
        idx = rng.integers(0, len(groups), size=(min(BLOCK, draws-start), len(groups)))
        samples.extend((sums[idx].sum(1)/counts[idx].sum(1)).tolist())
    s = np.asarray(samples)
    a = (1-LEVEL_BONF)/2
    return dict(value=float(sums.sum()/counts.sum()), ci95=np.quantile(s, [.025, .975]).tolist(),
                ci99375=np.quantile(s, [a, 1-a]).tolist(), n=int(counts.sum()), rooms=len(groups))


def swap(base, arm, flagged_ids):
    """Per-item swapped scores: arm's on flagged items, the baseline's elsewhere. Refuses missing keys."""
    if set(base) != set(arm):
        raise KeyError('arm and baseline keys differ (%d missing, %d extra)' % (len(set(base)-set(arm)), len(set(arm)-set(base))))
    if not set(flagged_ids) <= set(base):
        raise KeyError('flagged id outside the type')
    return {i: (arm[i] if i in flagged_ids else base[i]) for i in base}


def decidable(n_items, n_rooms, total):
    ceil = 100.0*n_items/total
    dec = n_items >= MIN_ITEMS and n_rooms >= MIN_ROOMS and ceil >= MIN_CEIL
    can_pass = dec and n_rooms >= MIN_PASS_ROOMS
    label = 'can pass or close' if can_pass else 'can close, cannot pass' if dec else 'too few to decide'
    return dict(items=n_items, rooms=n_rooms, ceiling_points=ceil, decidable=dec, can_pass=can_pass, label=label)


def price_type(ids, room, flagged_ids, scores, baselines):
    """scores: arm -> {id: score in [0,1]}; baselines: list of baseline arm names (first is the primary one)."""
    out = dict(n=len(ids), flagged=len(flagged_ids), by_baseline={})
    fl_rooms = {room[i] for i in flagged_ids}
    out['decidability'] = decidable(len(flagged_ids), len(fl_rooms), len(ids))
    for b in baselines:
        base = scores[b]
        rec = dict(baseline_score=100*sum(base[i] for i in ids)/len(ids), arms={})
        for a in ARMS:
            sw = swap(base, scores[a], flagged_ids)
            d = bootstrap([(room[i], 100*(sw[i]-base[i])) for i in ids])
            rec['arms'][a] = dict(swap_score=100*sum(sw.values())/len(ids), diff=d['value'], ci95=d['ci95'], ci99375=d['ci99375'],
                                  rooms=d['rooms'], flagged_changed=sum(sw[i] != base[i] for i in flagged_ids),
                                  unflagged_changed=sum(sw[i] != base[i] for i in ids if i not in flagged_ids),
                                  passes=d['value'] >= BAR and d['ci99375'][0] > 0, closes=d['ci95'][1] < BAR)
        orc = {i: (max(base[i], scores['own'][i], scores['direct'][i]) if i in flagged_ids else base[i]) for i in ids}
        d = bootstrap([(room[i], 100*(orc[i]-base[i])) for i in ids])
        rec['oracle'] = dict(swap_score=100*sum(orc.values())/len(ids), diff=d['value'], ci95=d['ci95'], ci99375=d['ci99375'])
        out['by_baseline'][b] = rec
    return out


def reading(types, anchors_checked):
    """Registered reading over per-type results (types: kind -> price_type output)."""
    dec = [k for k, v in types.items() if v['decidability']['decidable']]
    passes, held = [], []
    for k in dec:
        if not types[k]['decidability'].get('can_pass', False):
            continue
        bys = types[k]['by_baseline']
        for a in ARMS:
            if all(bys[b]['arms'][a]['passes'] for b in bys):
                (held if (a == 'direct' and not anchors_checked) else passes).append(dict(type=k, arm=a, diff=bys[next(iter(bys))]['arms'][a]['diff']))
    closed = bool(dec) and all(all(types[k]['by_baseline'][b]['arms'][a]['closes'] for b in types[k]['by_baseline'] for a in ARMS) for k in dec)
    if not dec:
        verdict = 'too few'
    elif passes:
        verdict = 'worth building'
    elif closed:
        verdict = 'closed'
    else:
        verdict = 'undecided'
    return dict(verdict=verdict, decidable_types=dec, passes=passes, passes_held_for_frames=held,
                cannot_pass_types=[k for k in dec if not types[k]['decidability'].get('can_pass', False)],
                too_few_types=[k for k in types if k not in dec])


def item_scores(items, arms):
    item_score, _ = C.item_score_fn()
    out = defaultdict(dict)
    for kind in C.TYPES:
        for arm in ('base', 'side', 'own'):
            if kind in arms[arm]:
                out[arm][kind] = {i: item_score(r['output'])[0] for i, r in arms[arm][kind].items()}
        out['direct'][kind] = {i: (0.0 if (r['hit_token_cap'] or r['parse_failed'] or r['finish_reason'] in ('length', 'error'))
                                   else float(r['score'])) for i, r in arms['direct'][kind].items()}
    for arm, per in out.items():
        for kind, s in per.items():
            if any(not (0.0 <= v <= 1.0) for v in s.values()):
                raise ValueError('score outside [0, 1]: %s %s' % (arm, kind))
    return out


def price_all(items, scores, flagged_caps, anchors_checked):
    types = {}
    for kind in C.TYPES:
        ids = C.type_ids(items, kind)
        room = {i: items[i]['room_key'] for i in ids}
        fl = {i for i in ids if items[i]['scene'] in flagged_caps}
        sc = dict(base=scores['base'][kind], own=scores['own'][kind], direct=scores['direct'][kind])
        bl = ['base']
        if kind in scores['side']:
            sc['side'] = scores['side'][kind]
            bl.append('side')
        types[kind] = price_type(ids, room, fl, sc, bl)
    return dict(types=types, reading=reading(types, anchors_checked))


BASE_LABEL = {('object_abs_distance', 'base'): '171253 read 1 (pinned candidates_argmax)',
              ('object_abs_distance', 'side'): '171253 read 0 (null_argmax; registered 26.93)'}


def named(passes):
    return ', '.join('%s with %s (%+.2f)' % (p['type'], ARM_NAME[p['arm']], p['diff']) for p in passes) or 'none'


def markdown(res):
    L = ['# STAB pricing: swap an untrusted tower call (K5 disagreement > tau) for another arm, dev-S1 (points)', '',
         'tau = %.4f deg (%s); flagged captures %d; anchors of the direct read: %s.' % (
             res['tau_deg'], 'void-fit fallback' if res['void_fit'] else 'Youden fit on 40 captures', len(res['flagged_captures']),
             res['frames']['direct_anchor_level']), '',
         OWN_CAMERA_CAVEAT, '',
         '| type | label | baseline | flagged items / rooms | base | arm | swap - base [99.375%] | 95% | pass | oracle - base |',
         '|---|---|---|---|---|---|---|---|---|---|']
    for kind, v in res['primary']['types'].items():
        dd = v['decidability']
        for b, rec in v['by_baseline'].items():
            for a in ARMS:
                x = rec['arms'][a]
                L.append('| %s | %s | %s | %d / %d | %.2f | %s | %+.2f [%+.2f, %+.2f] | [%+.2f, %+.2f] | %s | %+.2f |' % (
                    kind, dd['label'], BASE_LABEL[(kind, b)] if (kind, b) in BASE_LABEL else '171253 read 0',
                    dd['items'], dd['rooms'], rec['baseline_score'], ARM_NAME[a], x['diff'], x['ci99375'][0], x['ci99375'][1],
                    x['ci95'][0], x['ci95'][1], x['passes'] if dd['can_pass'] else 'no (cannot pass)', rec['oracle']['diff']))
    r, f = res['primary']['reading'], res['fragile_flipped']['reading']
    labels = '; '.join('%s: %s' % (k, v['decidability']['label']) for k, v in res['primary']['types'].items())
    flabels = '; '.join('%s: %s' % (k, v['decidability']['label']) for k, v in res['fragile_flipped']['types'].items())
    L += ['', 'Type labels: %s.' % labels,
        '**Reading as registered: %s.** Decidable types: %s. Passes: %s. Passes held for unchecked direct frames: %s.' % (
        r['verdict'], ', '.join(r['decidable_types']) or 'none', named(r['passes']), named(r['passes_held_for_frames'])),
        'Fragile-flag sensitivity (%d captures with tau/2 <= disagreement <= 2 tau flipped): %s; labels %s; passes %s. Reading %s under the flip.' % (
            len(res['fragile_captures']), f['verdict'], flabels, named(f['passes']),
            'holds' if f['verdict'] == r['verdict'] else 'CHANGES'),
        'Rules: ' + ' '.join(__doc__.split('\n', 2)[2].split())]
    return '\n'.join(L)+'\n'


def main(argv=None, stab=C.STAB, reg=C.REG):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)   # no options: output always goes to stab/code
    go = guard(stab)                                   # nothing is read before this line
    out = Path(stab)/'code'
    if (out/'PRICE_STAB.json').exists() or (out/'PRICE_STAB.md').exists():
        raise Refused('refused: PRICE_STAB.json or PRICE_STAB.md exists in %s; pricing runs once' % out)
    tau_raw = C.TAU_JSON.read_bytes()
    got = __import__('hashlib').sha256(tau_raw).hexdigest()
    if got != C.TAU_SHA256:
        raise Refused('refused: TAU.json sha256 %s differs from the pinned %s' % (got, C.TAU_SHA256))
    inputs = C.verify([k for k in reg if k not in ('nogt_tar5', 'nogt_tar6')], reg)
    inputs['score_nfa'] = C.item_score_fn()[1]
    tau = json.loads(tau_raw)
    items = C.load_items(reg)
    arms = C.load_arm_rows(reg)
    joins = C.join(items, arms)                        # refuses any missing or extra key
    direct_frames = json.loads(C.DIRECT_FRAMES.read_text()) if C.DIRECT_FRAMES.is_file() else None
    frames = C.frame_checks(items, arms, direct_frames)  # refuses any frame inequality, before any score
    scores = item_scores(items, arms)                  # first score read
    flagged = set(tau['flags']['list'])
    fragile = set(tau['fragile']['list'])
    flipped = (flagged - fragile) | (fragile - flagged)
    anchors = direct_frames is not None
    res = dict(schema='stab-price-v1', registration='DESIGN_STAB.md (lane lever7, 2026-11-21)', review_go=dict(path=str(go), sha256=C.sha(go)),
               tau_deg=tau['tau_deg'], void_fit=tau['void_fit'], tau_json_sha256=got,
               flagged_captures=sorted(flagged), fragile_captures=sorted(fragile), joins=joins, frames=frames,
               primary=price_all(items, scores, flagged, anchors), fragile_flipped=price_all(items, scores, flipped, anchors),
               bootstrap=dict(draws=DRAWS, seed=SEED, unit='room_key', estimator='ratio of sums (h1eval.statistics.bootstrap)',
                              levels=dict(bonferroni=LEVEL_BONF, closed=0.95)),
               rules=' '.join(__doc__.split('\n', 2)[2].split()), inputs=inputs)
    res['fragile_flipped']['reading_changes'] = res['fragile_flipped']['reading']['verdict'] != res['primary']['reading']['verdict']
    text, md = json.dumps(res, indent=1, allow_nan=False)+'\n', markdown(res)   # both composed before either is written
    out.mkdir(parents=True, exist_ok=True)
    (out/'PRICE_STAB.json').write_text(text)
    (out/'PRICE_STAB.md').write_text(md)
    print((out/'PRICE_STAB.md').read_text())
    return res


if __name__ == '__main__':
    try:
        main()
    except Refused as e:
        print(e, file=sys.stderr)
        sys.exit(2)
