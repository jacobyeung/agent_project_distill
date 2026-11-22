"""J1 step 4 (CPU, p1cpu): cells h1, h0 and k through relift.py's own fit_lift, gap, MRA and room bootstrap, paired with a and e
on relift's 117 eligible items inside dump 174135 (depth lever1_c/r1/returned/0.gz, receipt 4.json; T1 rows cont_ops24_c/cap/t1.gz).

relift.py is imported unchanged (j1_common.load_relift). a (served selected masks) and e (bound GT instance) are computed here
by the same code path and must equal a fresh in-process relift.run item by item (cells and gaps), and relift.stats over its rows
must equal the fresh statistics; the checks raise without showing a value.
Arms (select_j1 has the rules and the served contract with file:line):
  h1  per anchor, the top retained text proposal by score x presence if joint >= 0.05 and score >= 0.3; else empty.
  h0  per anchor, the retained text proposal with the highest IoU against the bound GT instance, if IoU >= 0.5; else empty.
  k   per anchor where GT is non-empty, SAM 3's top-scoring mask for the GT tight box; else empty.
Parity stop (before any h1/h0 cell): over every (item, operand, anchor) whose T1 row holds the model's ground call, J1's retained
  proposals must match the dump's (the masks cells c and d read, obj['proposals']) by select_j1.frame_match on >= 95% of
  operand-frames: a one-to-one IoU >= 0.95 pairing at 480x640 covers every proposal on either side with score >= 0.3 and
  score x presence >= 0.06; proposals under either level may stay unpaired; two empty lists match. The strict rule (same count,
  every proposal paired) is reported beside it. Below the bar, h1 and h0 are not computed and the result says so; k is read.
Pick-agreement gate (per arm, review finding 3.1): on the same operand-frames, h1's rule and h0's rule are applied to J1's pool
  and to the dump's pool; the picks agree when their 480x640 masks have IoU >= 0.95 or both are empty. An arm is read only when
  the pool gate passes and its picks agree on >= 95%; otherwise its status says why, and k is still read. parity.picks holds the
  counts.
Reading (fixed before any value exists), for X in h1, h0, k, on all 117 items (the only population that decides):
  X - a with relift's Bootstrap (10,000 physical-room draws, seed 20261120, item weighting); share (X-a)/(e-a) (ratio of item means,
  interval from the same draws); verdict: X - a >= 8 with lower bound > 0 -> source (h0, k: opens); X - a <= 4 with upper bound
  < 8 -> closes; else undecided. Per dataset (ARKit, ScanNet, ScanNet++), the same numbers with item and room counts, not deciding.
  Per-frame precision/recall at the anchors against the bound GT instance for a, e, h1, h0, k per dataset, over (item, operand,
  anchor) with GT or prediction non-empty: precision = mean |P&G|/|P| over anchors with P non-empty; recall = mean |P&G|/|G| over
  anchors with G non-empty; plus the count of anchors where the arm has a mask and GT is empty.
  For each undecided arm: select_j1.needed_items (paired items and rooms to clear the nearer bar at the observed per-room spread
  and mean) and the rooms that could supply them: the manifest's items outside the 117 with relift's exclusion reasons. R0-dev
  stays unspent.
Outputs: out/RELIFT_J1.json, out/RELIFT_J1.md, out/ITEMS_J1.jsonl (one row per item and arm in a, e, h1, h0, k). Prints the status.
Usage: cd j1/kit && CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B relift_j1.py [--detect ../out/detect]
"""
import argparse, contextlib, io, json, sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import j1_common as G
import select_j1 as S

ARMS = ('h1', 'h0', 'k')
CELLS = ('a', 'e') + ARMS
ORACLE = {'h0': True, 'k': True, 'h1': False}
REFUSAL = 'parity below 95% of operand-frames: h1 and h0 are not read; k is read'


def gates(par):
    """(text arms to read, status) from the pool gate and each arm's pick-agreement gate."""
    read, why = [], []
    for k in ('h1', 'h0'):
        if not par['passed']:
            why.append('%s not read: pool parity %d/%d below 95%%' % (k, par['matched'], par['operand_frames']))
        elif not par['picks'][k]['passed']:
            why.append('%s not read: %s picks agree on %d/%d operand-frames, below 95%%' % (k, k, par['picks'][k]['agree'], par['picks'][k]['operand_frames']))
        else:
            read.append(k)
    return read, 'complete' if not why else 'complete (%s; k is read)' % '; '.join(why)


# ---------------------------------------------------------------- relift

def relift_args(R, out):
    return SimpleNamespace(capture=R.BASE/'cap/t1.gz', depth=G.DEPTH, receipt=G.RECEIPT, join=R.BASE/'cap/score_t1/JOIN_T1.jsonl',
                           funnel=R.BASE/'cap/score_t1/FUNNEL_T1.json',
                           gt_dirs=[R.BASE/'gt/t1_gt/gt', R.BASE/'gt/arkit_gt/gt']+R.NOGT_DIRS, out=Path(out), half_only=False)


def fresh_relift(R):
    """relift.run on the registered inputs, its JSON dump captured in memory and its stdout swallowed (lever7 relift_t.py)."""
    captured = {}
    original = R.dump
    R.dump = lambda path, value: captured.__setitem__('result', value)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            R.run(relift_args(R, G.OUT/'unused_relift_dump.json'))
    finally:
        R.dump = original
    result = captured['result']
    if result['status'] != 'complete':
        raise ValueError('fresh relift did not complete: '+str(result['status']))
    return result


def upsample(mask240):
    """Grid mask -> 480x640 by pixel doubling; to_grid recovers it exactly (used by the toy stores in the tests)."""
    return np.repeat(np.repeat(np.asarray(mask240, bool), 2, 0), 2, 1)


# ---------------------------------------------------------------- detector store

class DetectStore:
    """The GPU job's per-capture files under one contract, on the current FRAMES_J1 and PROMPTS_J1, all 32 anchors.
    capture(cap) -> dict(text={prompt: [32 lists of dict(score, presence, mask480)]}, k={instance_id: (32,240,320) bool})."""

    def __init__(self, detect_dir, prompts):
        self.dir = Path(detect_dir); self.prompts = {c['capture']: c for c in prompts['captures']}; contracts = set()
        fsha, psha = G.sha256_file(G.FRAMES_J1), G.sha256_file(G.PROMPTS_J1)
        self.paths = {}
        for cap in self.prompts:
            p = self.dir/(G.stub(cap)+'.json.gz')
            if not p.is_file():
                raise FileNotFoundError('missing detector file '+str(p))
            self.paths[cap] = p
        index = G.read_json(self.dir/'INDEX.json') if (self.dir/'INDEX.json').is_file() else None
        if index is None or index['failed'] or index['stopped'] or index['done'] != len(self.prompts):
            raise ValueError('detector INDEX.json is missing or reports failed, stopped or unfinished captures')
        for cap, p in self.paths.items():
            d = G.read_json(p)
            c = d['contract']
            if c['frames_j1_sha256'] != fsha or c['prompts_j1_sha256'] != psha or c['anchor_limit'] != 32 or d['anchors'] != 32 or d['capture'] != cap:
                raise ValueError('detector file not on the current frames/prompts or not on all 32 anchors: '+str(p))
            if set(d['text']) != set(self.prompts[cap]['prompts']) or {int(x) for x in d['k']} != {u['instance_id'] for u in self.prompts[cap]['k_units']}:
                raise ValueError('detector file prompts or k units differ from PROMPTS_J1: '+str(p))
            contracts.add(G.digest(c))
        if len(contracts) != 1:
            raise ValueError('detector files written under %d contracts' % len(contracts))
        self.contract = contracts.pop(); self._cache = {}

    def capture(self, cap):
        if cap not in self._cache:
            self._cache.clear()
            d = G.read_json(self.paths[cap])
            text = {p: [[dict(score=e['score'], presence=e['presence'], mask480=G.unpack(e['mask'])) for e in fr] for fr in frames]
                    for p, frames in d['text'].items()}
            units = {u['instance_id']: u for u in self.prompts[cap]['k_units']}
            k = {}
            for key, rec in d['k'].items():
                iid = int(key)
                if rec['gt_sha256'] != units[iid]['gt_sha256'] or [a['slot'] for a in rec['anchors']] != [b['slot'] for b in units[iid]['boxes']]:
                    raise ValueError('k unit differs from PROMPTS_J1: %s %d' % (cap, iid))
                m = np.zeros((32,)+G.GRID, bool)
                for a in rec['anchors']:
                    m[a['slot']-1] = S.to_grid(G.unpack(a['mask']))
                k[iid] = m
            self._cache[cap] = dict(text=text, k=k)
        return self._cache[cap]


# ---------------------------------------------------------------- parity

def dump_frames(R, obj):
    """The dump's retained proposals of one operand per anchor (stored order): dict(mask480, score, presence)."""
    out = [[] for _ in range(32)]
    for p in obj['proposals']:
        out[int(p['frame'])-1].append(dict(mask480=R.unrle(p['mask']), score=float(p['score']), presence=float(p['presence'])))
    return out


def parity(R, rows, items, objects, store):
    """Fraction of operand-frames (operands with a T1 ground call) whose J1 pool matches the dump pool under the registered rule
    (select_j1.frame_match), with the strict rule (same count, all paired) beside it."""
    by_item = {}
    for o in objects:
        by_item.setdefault(o['item_id'], []).append(o)
    counts = {d: dict(frames=0, matched=0, strict=0, unpaired_clear_frames=0, h1_agree=0, h0_agree=0) for d in G.DATASETS3}
    no_call = 0; worst = []; inst_cap = [None, None]
    for it in items:
        cap = it['capture']; served = {o['name'].strip().lower(): o for o in rows[it['item_id']]['objects']}
        text = store.capture(cap)['text']
        if inst_cap[0] != cap:
            with np.load(it['gt_path'], allow_pickle=False) as z:
                inst_cap[:] = [cap, z['inst'].copy()]
        inst = inst_cap[1]
        for o in by_item[it['item_id']]:
            obj = served.get(o['name'].strip().lower())
            if obj is None:
                no_call += 1; continue
            theirs = dump_frames(R, obj); mine = text[o['name'].strip().lower()]
            c = counts[G.fine(cap)]; target = inst == o['instance_id']
            for f in range(32):
                agree = S.pick_match(mine[f], theirs[f], target[f])
                c['h1_agree'] += agree['h1']; c['h0_agree'] += agree['h0']
                ok, why = S.frame_match(mine[f], theirs[f])
                c['frames'] += 1; c['matched'] += ok; c['strict'] += why['strict']; c['unpaired_clear_frames'] += not ok
                if why.get('min_pair_iou') is not None:
                    worst.append(why['min_pair_iou'])
    frames = sum(c['frames'] for c in counts.values()); matched = sum(c['matched'] for c in counts.values())
    strict = sum(c['strict'] for c in counts.values())
    fraction = matched/frames if frames else 0.
    picks = {}
    for k in ('h1', 'h0'):
        n = sum(c[k+'_agree'] for c in counts.values()); fr = n/frames if frames else 0.
        picks[k] = dict(agree=n, operand_frames=frames, fraction=fr, passed=fr >= S.PARITY_BAR)
    return dict(picks=picks, pick_rule=S.__doc__.split('Pick agreement (pick_match, a second gate per arm, review finding 3.1): ')[1].strip(), rule=S.__doc__.split('Parity (frame_match, the registered gate): ')[1].strip(), bar=S.PARITY_BAR, iou=S.PARITY_IOU,
                operand_frames=frames, matched=matched, fraction=fraction, passed=fraction >= S.PARITY_BAR,
                strict_matched=strict, strict_fraction=strict/frames if frames else 0., operands_without_ground_call=no_call,
                min_pair_iou=min(worst, default=None), by_dataset=counts)


# ---------------------------------------------------------------- cells

def share(boot, rr, k):
    """(k-a)/(e-a): ratio of item means, and per bootstrap draw the ratio of the drawn means (lever7 relift_t.py)."""
    dk = [dict(r, delta=r[k]-r['a']) for r in rr]; de = [dict(r, delta=r['e']-r['a']) for r in rr]
    vk, _ = boot.samples(dk, 'delta'); ve, _ = boot.samples(de, 'delta')
    ratio = np.divide(vk, ve, out=np.full(len(vk), np.nan), where=np.isfinite(ve) & (ve != 0))
    mk = float(np.mean([r['delta'] for r in dk])) if rr else None; me = float(np.mean([r['delta'] for r in de])) if rr else None
    return boot.summarize(mk/me if me else None, ratio)


def compute(R, fresh, store, read_text):
    """Rows, per-item records and statistics. read_text: True (h1 and h0), False (neither) or the set of text arms whose gates
    passed; an arm left out appears nowhere."""
    refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
    items, objects, _ = G.eligible(R, refs)
    rows = R.read_records(R.BASE/'cap/t1.gz', refs)
    depths = G.depth_rows(R)
    text_arms = ('h1', 'h0') if read_text is True else () if not read_text else tuple(a for a in ('h1', 'h0') if a in read_text)
    arms = text_arms + ('k',)
    cells = ('a', 'e') + arms
    by_item = {}
    for o in objects:
        by_item.setdefault(o['item_id'], []).append(o)
    out, records, pr, cache = [], [], {(k, d): [] for k in cells for d in G.DATASETS3}, {}
    for it in items:
        iid, cap = it['item_id'], it['capture']; ref = refs[iid]
        if cap not in cache:
            cache.clear()
            with np.load(it['gt_path'], allow_pickle=False) as z:
                cache[cap] = (z['inst'].copy(), R.restore(depths[cap]))
        inst, g = cache[cap]
        det = store.capture(cap)
        served = {o['name'].strip().lower(): o for o in rows[iid]['objects']}
        pair = {k: [] for k in cells}; operand_info = {k: [] for k in cells}
        for o in by_item[iid]:
            name = o['name']; target = inst == o['instance_id']; obj = served.get(name.strip().lower())
            masks = dict(a=R.masks_array(obj['selected_masks']) if obj else np.zeros((32,)+G.GRID, bool), e=target,
                         k=det['k'][o['instance_id']])
            if text_arms:
                frames = [[dict(p, mask240=S.to_grid(p['mask480'])) for p in fr] for fr in det['text'][name.strip().lower()]]
                if 'h1' in text_arms:
                    masks['h1'] = S.arm_h1(frames)
                if 'h0' in text_arms:
                    masks['h0'] = S.arm_h0(frames, target)
            for k in cells:
                if masks[k].shape != (32,)+G.GRID:
                    raise ValueError('mask grid differs for cell '+k)
                value, lift = R.fit_lift(name, masks[k], g)
                pair[k].append(value)
                fr = G.precision_recall(masks[k], target); pr[(k, G.fine(cap))] += fr
                operand_info[k].append(dict(name=name, prompt=name.strip().lower(), instance_id=o['instance_id'], served_call=obj is not None,
                                            frames_with_mask=[f+1 for f in range(32) if masks[k][f].any()],
                                            frames_with_gt=[f+1 for f in range(32) if target[f].any()],
                                            pr=G.summarize_pr(fr), lift_best=lift.get('best') if lift else None))
        truth = float(ref['task']['ground_truth']); factor = R.unit_factor(ref['task']['question'])
        entry = dict(item_id=iid, capture=cap, room=ref['task']['room'], dataset=G.dataset(cap), dataset3=G.fine(cap), gaps={})
        for k, values in pair.items():
            lifted = R.gap_value(values); gap = R.round_gap(lifted); entry['gaps'][k] = gap
            entry[k] = 100*R.official_mra(None if gap is None else gap*factor, truth)
            records.append(dict(item_id=iid, arm=k, room=entry['room'], dataset=entry['dataset3'], capture=cap,
                                type=ref['task']['question_type'], operands=operand_info[k], lifted_distance_m=lifted,
                                printed_gap_m=gap, printed_answer=None if gap is None else gap*factor, unit_factor=factor,
                                gt=truth, score=entry[k]))
        out.append(entry)
    # a and e reproduce relift's own cells, item by item and in order; relift.stats over the fresh rows is the fresh statistics.
    ref_rows = fresh['rows']
    if [r['item_id'] for r in ref_rows] != [r['item_id'] for r in out]:
        raise AssertionError('item population or order differs from relift')
    for mine, theirs in zip(out, ref_rows):
        for k in ('a', 'e'):
            if mine[k] != theirs[k] or mine['gaps'][k] != theirs['gaps'][k]:
                raise AssertionError('cell %s differs from relift on %s' % (k, mine['item_id']))
    if R.stats([dict(t) for t in ref_rows], refs) != fresh['statistics']:
        raise AssertionError('relift.stats over the fresh rows differs from the fresh run')
    boot = R.Bootstrap(refs); statistics = []
    for ds in ('all',) + G.DATASETS3:
        rr = [r for r in out if ds == 'all' or r['dataset3'] == ds]
        s = dict(dataset=ds, n=len(rr), rooms=len({r['room'] for r in rr}), decides=ds == 'all',
                 cells={k: boot.metric(rr, k) for k in cells},
                 versus_a={k+'-a': boot.metric([dict(r, delta=r[k]-r['a']) for r in rr], 'delta') for k in arms+('e',)},
                 share_of_e_minus_a={k: share(boot, rr, k) for k in arms})
        if ds == 'all':
            s['verdict'] = {k: S.verdict(s['versus_a'][k+'-a'], ORACLE[k]) for k in arms}
        statistics.append(s)
    precision_recall = {k: {d: G.summarize_pr(pr[(k, d)]) for d in G.DATASETS3} for k in cells}
    for k in cells:
        precision_recall[k]['all'] = G.summarize_pr([x for d in G.DATASETS3 for x in pr[(k, d)]])
    verdicts = statistics[0]['verdict']
    for row in out:
        for k in arms:
            row[k+'_minus_a'] = row[k]-row['a']
    needed = {k: S.needed_items(out, k+'_minus_a') for k in arms if verdicts[k] == 'undecided'}
    for row in out:
        for k in arms:
            del row[k+'_minus_a']
    return dict(rows=out, records=records, statistics=statistics, precision_recall=precision_recall, verdict=verdicts, needed=needed,
                arms_read=list(arms), reproduction=dict(a_e_rows_equal=True, relift_stats_equal=True, items=len(out),
                                                       captures=len({r['capture'] for r in out})))


def supply(fresh, refs, rows117):
    """Manifest items outside the 117 that could add paired items, with relift's exclusion reasons and their rooms."""
    rooms117 = {r['room'] for r in rows117}; ex = []
    for e in fresh['exclusions']:
        ref = refs[e['item_id']]
        ex.append(dict(item_id=e['item_id'], reason=e['reason'], room=ref['task']['room'], capture=ref['capture'],
                       dataset=G.fine(ref['capture']), new_room=ref['task']['room'] not in rooms117))
    by_reason = {}
    for x in ex:
        b = by_reason.setdefault(x['reason'], dict(items=0, rooms=set(), new_rooms=set()))
        b['items'] += 1; b['rooms'].add(x['room'])
        if x['new_room']:
            b['new_rooms'].add(x['room'])
    return dict(excluded_items=ex, by_reason={k: dict(items=v['items'], rooms=len(v['rooms']), new_rooms=len(v['new_rooms']))
                                              for k, v in sorted(by_reason.items())},
                note='These are the manifest (items544) items relift excludes; each would need its exclusion lifted (GT capture, '
                     'operand binding or portrait orientation) before it pairs. R0-dev stays unspent.')


def markdown(res):
    L = ['# RELIFT_J1: SAM 3 frozen detector per frame (h1), pool oracle (h0), box oracle (k), paired inside dump 174135', '',
         'Status: %s. Parity: %d of %d operand-frames match (%.4f; bar 0.95; %s); strict rule (same count, all paired, not '
         'gating) %d (%.4f).' % (
             res['status'], res['parity']['matched'], res['parity']['operand_frames'], res['parity']['fraction'],
             'passed' if res['parity']['passed'] else 'FAILED: ' + REFUSAL, res['parity']['strict_matched'],
             res['parity']['strict_fraction']),
         'Pick agreement (h1, h0 rules on both pools; gate 0.95 each): ' + '; '.join('%s %d/%d (%s)' % (
             k, v['agree'], v['operand_frames'], 'passed' if v['passed'] else 'FAILED') for k, v in res['parity']['picks'].items()), '']
    def f(m):
        return 'n/a' if m['mean'] is None else '%+.1f [%+.1f, %+.1f]' % (m['mean'], *m['ci95'])
    L += ['| dataset | items | rooms | ' + ' | '.join(k+' - a' for k in res['arms_read']) + ' | e - a |', '|---|---|---|' + '---|'*(len(res['arms_read'])+1)]
    for s in res['statistics']:
        L.append('| %s%s | %d | %d | ' % (s['dataset'], ' (decides)' if s['decides'] else '', s['n'], s['rooms'])
                 + ' | '.join(f(s['versus_a'][k+'-a']) for k in res['arms_read']) + ' | ' + f(s['versus_a']['e-a']) + ' |')
    top = res['statistics'][0]
    L += ['', 'Verdicts (all 117 items): ' + '; '.join('%s %s (share of e-a %s)' % (k, res['verdict'][k],
          'n/a' if top['share_of_e_minus_a'][k]['mean'] is None else '%.2f' % top['share_of_e_minus_a'][k]['mean']) for k in res['arms_read']), '',
          '| arm | dataset | precision | recall | anchors with mask, GT empty |', '|---|---|---|---|---|']
    for k, v in res['precision_recall'].items():
        for d, x in v.items():
            L.append('| %s | %s | %s | %s | %d |' % (k, d, 'n/a' if x['precision'] is None else '%.3f' % x['precision'],
                                                  'n/a' if x['recall'] is None else '%.3f' % x['recall'], x['pred_on_empty_gt']))
    for k, v in res['needed'].items():
        L.append('')
        L.append('%s undecided: ' % k + (v.get('reason') if v.get('bar') is None else
                 'clearing the %s bar needs about %d paired items in %d rooms (now %d in %d)' % (v['bar'], v['items_needed'], v['rooms_needed'], v['items'], v['rooms'])))
    L += ['', 'Supply outside the 117: ' + '; '.join('%s: %d items, %d rooms (%d new)' % (k, v['items'], v['rooms'], v['new_rooms'])
                                                    for k, v in res['supply']['by_reason'].items()) + '. R0-dev stays unspent.']
    return '\n'.join(L)+'\n'


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--detect', type=Path, default=G.DETECT)
    ap.add_argument('--out', type=Path, default=G.OUT/'RELIFT_J1.json')
    ap.add_argument('--items-out', type=Path, default=G.OUT/'ITEMS_J1.jsonl')
    args = ap.parse_args(argv)
    R = G.load_relift(); R.dependencies()
    prompts = G.read_json(G.PROMPTS_J1)
    store = DetectStore(args.detect, prompts)
    refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
    items, objects, _ = G.eligible(R, refs)
    rows = R.read_records(R.BASE/'cap/t1.gz', refs)
    par = parity(R, rows, items, objects, store)
    fresh = fresh_relift(R)
    read, status = gates(par)
    res = compute(R, fresh, store, set(read))
    records = res.pop('records')
    res.update(status=status, parity=par, supply=supply(fresh, refs, res['rows']),
               detect=str(args.detect), detect_contract_digest=store.contract,
               definitions=dict(h1=S.__doc__.split('Arms')[1].split('Parity')[0].strip(), parity=S.frame_match.__doc__,
                                reading=__doc__.split('Reading (fixed before any value exists), ')[1].split('Outputs:')[0].strip(),
                                bootstrap='relift Bootstrap: 10,000 physical-room draws, seed 20261120, item weighting'),
               input_sha256={str(p): G.sha256_file(p) for p in (G.RELIFT, G.DEPTH, G.RECEIPT, G.ITEMS, G.FRAMES_J1, G.PROMPTS_J1, Path(__file__),
                                                                 Path(S.__file__))})
    G.write_json(args.out, res)
    args.out.with_suffix('.md').write_text(markdown(res))
    args.items_out.parent.mkdir(parents=True, exist_ok=True)
    with args.items_out.open('w') as f:
        for r in records:
            f.write(G.dumps_plain(r)+'\n')
    print(res['status'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
