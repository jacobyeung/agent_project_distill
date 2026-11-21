"""GTC-B step 3: cells t, s and b through relift.py's own fit_lift, gap, MRA and bootstrap, paired with a and e on its 117 items.

Copy of the GTC kit's relift_t.py. t and s are computed exactly as there, from the read-only GTC tracks (lever6/gtc/out/track,
seeds lever6/gtc/out/SEEDS_GTC.json), and every t/s output (rows, statistics, precision/recall, reading, reproduction) must
equal lever6/gtc/out/RELIFT_GTC.json; the check compares and never prints. Arm b (t_big) comes from lever6/gtcb/out/track
(seeds out/SEEDS_GTCB.json) through the same fit_lift, round_gap(gap_value), official_mra x 100.
relift.py (lever5/r1x/r1, review GO) is imported unchanged from its path. The wrapper
  1. runs relift.run in-process for the reference cells and asserts a and e (and relift.stats) equal it, as in GTC;
  2. computes a, e, t, s, b per item; the GTC fields keep their GTC form (cells a, e, t, s; t-a, s-a, e-a; shares; seed200;
     precision/recall of t and s; the t reading);
  3. adds the section 'b', overall and per dataset (relift's split: ARKit, ScanNet/ScanNet++), with relift's Bootstrap
     (10,000 physical-room draws, seed 20261120, item weighting): cell b, b-a, b-t (descriptive), e-a, share (b-a)/(e-a);
     per-frame mask precision/recall of b against the bound GT instance; the b seed facts from SEEDS_GTCB (median area,
     count under 200 px); and the registered reading on b-a over all 117 items as the field 'reading' (no seed-size guard).
Per-frame precision/recall: over every (item, operand) and anchor where the GT instance or the prediction is nonempty;
  precision = |P&G|/|P| averaged over those frames with P nonempty; recall = |P&G|/|G| averaged over those with G nonempty.
Usage (p1cpu): python relift_t.py            (defaults: t/s tracks gtc/out/track, b tracks gtcb/out/track,
                                             out gtcb/out/RELIFT_GTCB.json; prints only the status)
"""
import argparse, contextlib, io, json, sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gtc_common as G

CELLS = ('a', 'e', 't', 's')
SEED_MIN_AREA = 200
VERDICTS = ('source_once_seed_right', 'not_the_source', 'undecided')
B_VERDICTS = ('source_when_seeded_on_best_frame', 'not_the_source', 'undecided')


def seed200_items(seeds):
    """Item ids in the seed-size subset, from SEEDS_GTC alone: every operand of the item has t status OK and area_240 >= 200."""
    area = {(c['capture'], u['unit']): u['area_240'] for c in seeds['captures'] for u in c['units'] if u['arm'] == 't'}
    ok = {}
    for o in seeds['objects']:
        good = o['t']['status'] == 'OK' and area[(o['capture'], o['t']['unit'])] >= SEED_MIN_AREA
        ok[o['item_id']] = ok.get(o['item_id'], True) and good
    return {i for i, v in ok.items() if v}


def meets_first_bar(m):
    """Registered first bar: mean >= 8 and 95% lower bound > 0."""
    return m['mean'] is not None and m['ci95'] is not None and m['mean'] >= 8 and m['ci95'][0] > 0


def meets_second_bar(m):
    """Registered 'not the source' bar: mean <= 4 and 95% upper bound < 8."""
    return m['mean'] is not None and m['ci95'] is not None and m['mean'] <= 4 and m['ci95'][1] < 8


def reading(full, subset, s_full=None):
    """Registered reading from t-a on all items (full) and on the seed-size subset (subset). Returns dict(verdict, reason)."""
    if meets_first_bar(full):
        out = dict(verdict='source_once_seed_right', reason='t-a on all items >= 8 with lower bound > 0')
        if s_full is not None:
            out['s_minus_a_meets_first_bar'] = meets_first_bar(s_full)
        return out
    if meets_second_bar(full):
        if meets_first_bar(subset):
            return dict(verdict='undecided', reason='seed-size guard: t-a on all items <= 4 with upper bound < 8, but the '
                                                    '>=200-pixel seed subset shows t-a >= 8 with lower bound > 0')
        return dict(verdict='not_the_source', reason='t-a on all items <= 4 with upper bound < 8; the >=200-pixel seed subset '
                                                     'does not show t-a >= 8 with lower bound > 0')
    return dict(verdict='undecided', reason='t-a on all items meets neither bar')


def reading_b(full):
    """Registered GTC-B reading from b-a on all 117 items: the bars of t, no seed-size guard. Returns dict(verdict, reason)."""
    if meets_first_bar(full):
        return dict(verdict='source_when_seeded_on_best_frame', reason='b-a on all items >= 8 with lower bound > 0')
    if meets_second_bar(full):
        return dict(verdict='not_the_source', reason='b-a on all items <= 4 with upper bound < 8')
    return dict(verdict='undecided', reason='b-a on all items meets neither bar')


def relift_args(R, out):
    return SimpleNamespace(capture=R.BASE/'cap/t1.gz', depth=G.DEPTH, receipt=G.RECEIPT, join=R.BASE/'cap/score_t1/JOIN_T1.jsonl',
                           funnel=R.BASE/'cap/score_t1/FUNNEL_T1.json',
                           gt_dirs=[R.BASE/'gt/t1_gt/gt', R.BASE/'gt/arkit_gt/gt']+R.NOGT_DIRS, out=Path(out), half_only=False)


def fresh_relift(R):
    """relift.run on the registered inputs, its JSON dump captured in memory and its stdout swallowed."""
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


def track_source(track_dir, seeds_path=G.SEEDS_TS, arms=G.ARMS):
    """source(arm, ctx) -> (32,240,320) tracker masks of the operand's unit; zeros when the arm has no seed.
    Requires every (arm, capture) file of the given arms under one contract on the given seeds file and all 32 anchors.
    t, s: track_source(gtc/out/track) on SEEDS_GTC; b: track_source(gtcb/out/track, SEEDS_GTCB, ('b',))."""
    seeds = G.read_json(seeds_path); seeds_sha = G.sha256_file(seeds_path)
    by_obj = {(o['item_id'], o['name']): o for o in seeds['objects']}
    units, contracts = {}, set()
    for c in seeds['captures']:
        for arm in arms:
            if not any(u['arm'] == arm for u in c['units']):
                continue
            path = Path(track_dir)/arm/(G.stub(c['capture'])+'.json.gz')
            if not path.exists():
                raise FileNotFoundError('missing track file '+str(path))
            d = G.read_json(path)
            if d['contract']['seeds_sha256'] != seeds_sha or d['anchors'] != 32 or d['skipped_units']:
                raise ValueError('track file not on the current seeds or not on all 32 anchors: '+str(path))
            contracts.add(G.digest(d['contract']))
            want = {u['unit'] for u in c['units'] if u['arm'] == arm}
            if {u['unit'] for u in d['units']} != want:
                raise ValueError('track file units differ from the seeds file: '+str(path))
            for u in d['units']:
                units[(c['capture'], arm, u['unit'])] = G.unpack(u['masks'])
    if len(contracts) != 1:
        raise ValueError('track files written under %d contracts' % len(contracts))

    def source(arm, ctx):
        o = by_obj[(ctx['item_id'], ctx['name'])]
        if o[arm]['status'] != 'OK':
            return np.zeros((32,)+G.GRID, bool)
        return units[(ctx['capture'], arm, o[arm]['unit'])]
    source.contract = contracts.pop()
    return source


def share(boot, rr, k):
    """(k-a)/(e-a): ratio of item means, and per bootstrap draw the ratio of the drawn means."""
    dk = [dict(r, delta=r[k]-r['a']) for r in rr]; de = [dict(r, delta=r['e']-r['a']) for r in rr]
    vk, _ = boot.samples(dk, 'delta'); ve, _ = boot.samples(de, 'delta')
    ratio = np.divide(vk, ve, out=np.full(len(vk), np.nan), where=np.isfinite(ve) & (ve != 0))
    mk = float(np.mean([r['delta'] for r in dk])) if rr else None; me = float(np.mean([r['delta'] for r in de])) if rr else None
    return boot.summarize(mk/me if me else None, ratio)


def compute(R, fresh, source, source_b, seeds_path=G.SEEDS_TS, seeds_b_path=G.SEEDS_B):
    """Rows and statistics for a, e, t, s, the seed-size subset and the registered t reading (GTC form), plus the section 'b'.
    Asserts a and e (and relift.stats) equal the fresh relift run. Returns a dict."""
    seeds = G.read_json(seeds_path); seeds_b = G.read_json(seeds_b_path)
    seed_obj = {(o['item_id'], o['name']): o for o in seeds['objects']}
    seed_area = {(c['capture'], u['unit']): u['area_240'] for c in seeds['captures'] for u in c['units'] if u['arm'] == 't'}
    refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
    items, objects, _ = G.eligible(R, refs)
    rows = R.read_records(R.BASE/'cap/t1.gz', refs)
    depths = G.depth_rows(R)
    by_item = {}
    for o in objects:
        by_item.setdefault(o['item_id'], []).append(o)
    out, pr, cache = [], {('t', d): [] for d in ('ARKit', 'ScanNet/ScanNet++')}, {}
    pr.update({(k, d): [] for k in ('s', 'b') for d in ('ARKit', 'ScanNet/ScanNet++')})
    for it in items:
        iid, cap = it['item_id'], it['capture']; ref = refs[iid]
        if cap not in cache:
            cache.clear()
            with np.load(it['gt_path'], allow_pickle=False) as z:
                cache[cap] = (z['inst'].copy(), R.restore(depths[cap]))
        inst, g = cache[cap]
        served = {o['name'].strip().lower(): o for o in rows[iid]['objects']}
        pair = {k: [] for k in CELLS+('b',)}
        for o in by_item[iid]:
            name = o['name']; target = inst == o['instance_id']; obj = served.get(name.strip().lower())
            sm = R.masks_array(obj['selected_masks']) if obj else np.zeros((32,)+G.GRID, bool)
            ctx = dict(item_id=iid, capture=cap, name=name, instance_id=o['instance_id'], target=target, served=sm)
            masks = dict(a=sm, e=target, t=np.asarray(source('t', ctx), bool), s=np.asarray(source('s', ctx), bool),
                         b=np.asarray(source_b('b', ctx), bool))
            for k in CELLS+('b',):
                if masks[k].shape != (32,)+G.GRID:
                    raise ValueError('mask grid differs for cell '+k)
                pair[k].append(R.fit_lift(name, masks[k], g)[0])
            for k in ('t', 's', 'b'):
                pr[(k, G.dataset(cap))] += G.precision_recall(masks[k], target)
        truth = float(ref['task']['ground_truth']); factor = R.unit_factor(ref['task']['question'])
        tseeds = [seed_obj[(iid, o['name'])]['t'] for o in by_item[iid]]
        seed200 = all(ts['status'] == 'OK' and seed_area[(cap, ts['unit'])] >= SEED_MIN_AREA for ts in tseeds)
        entry = dict(item_id=iid, capture=cap, room=ref['task']['room'], dataset=G.dataset(cap), seed200=seed200, gaps={})
        for k, values in pair.items():
            gap = R.round_gap(R.gap_value(values)); entry['gaps'][k] = gap
            entry[k] = 100*R.official_mra(None if gap is None else gap*factor, truth)
        out.append(entry)
    # Reproduction of relift's own cells a and e, item by item and in order.
    ref_rows = fresh['rows']
    if [r['item_id'] for r in ref_rows] != [r['item_id'] for r in out]:
        raise AssertionError('item population or order differs from relift')
    for mine, theirs in zip(out, ref_rows):
        for k in ('a', 'e'):
            if mine[k] != theirs[k] or mine['gaps'][k] != theirs['gaps'][k]:
                raise AssertionError('cell %s differs from relift on %s' % (k, mine['item_id']))
    merged = [dict(theirs, t=mine['t'], s=mine['s']) for mine, theirs in zip(out, ref_rows)]
    if R.stats(merged, refs) != fresh['statistics']:
        raise AssertionError('relift.stats over the fresh rows differs from the fresh run')
    boot = R.Bootstrap(refs); statistics = []
    for ds in ('all', 'ARKit', 'ScanNet/ScanNet++'):
        rr = [r for r in out if ds == 'all' or r['dataset'] == ds]
        statistics.append(dict(dataset=ds, n=len(rr), rooms=len({r['room'] for r in rr}),
                               cells={k: boot.metric(rr, k) for k in CELLS},
                               versus_a={k+'-a': boot.metric([dict(r, delta=r[k]-r['a']) for r in rr], 'delta') for k in ('t', 's', 'e')},
                               share_of_e_minus_a={k: share(boot, rr, k) for k in ('t', 's')}))
        sub = [r for r in rr if r['seed200']]
        statistics[-1]['seed200'] = dict(n=len(sub), rooms=len({r['room'] for r in sub}),
                                         t_minus_a=boot.metric([dict(r, delta=r['t']-r['a']) for r in sub], 'delta'))
    if {r['item_id'] for r in out if r['seed200']} != seed200_items(seeds) & {r['item_id'] for r in out}:
        raise AssertionError('seed-size subset differs from SEEDS_GTC')
    overall = statistics[0]
    verdict = reading(overall['versus_a']['t-a'], overall['seed200']['t_minus_a'], overall['versus_a']['s-a'])
    precision_recall = {k: {d: G.summarize_pr(pr[(k, d)]) for d in ('ARKit', 'ScanNet/ScanNet++')} for k in ('t', 's')}
    for k in ('t', 's'):
        precision_recall[k]['all'] = G.summarize_pr(pr[(k, 'ARKit')]+pr[(k, 'ScanNet/ScanNet++')])
    b_stats = []
    for ds in ('all', 'ARKit', 'ScanNet/ScanNet++'):
        rr = [r for r in out if ds == 'all' or r['dataset'] == ds]
        b_stats.append(dict(dataset=ds, n=len(rr), rooms=len({r['room'] for r in rr}), cell_b=boot.metric(rr, 'b'),
                            versus={k: boot.metric([dict(r, delta=r[k.split('-')[0]]-r[k.split('-')[1]]) for r in rr], 'delta')
                                    for k in ('b-a', 'b-t', 'e-a')},
                            share_of_e_minus_a=share(boot, rr, 'b')))
    pr_b = {d: G.summarize_pr(pr[('b', d)]) for d in ('ARKit', 'ScanNet/ScanNet++')}
    pr_b['all'] = G.summarize_pr(pr[('b', 'ARKit')]+pr[('b', 'ScanNet/ScanNet++')])
    b = dict(statistics=b_stats, precision_recall=pr_b, reading=reading_b(b_stats[0]['versus']['b-a']),
             seed_facts=dict(all=seeds_b['summary']['seed_facts'], **seeds_b['summary']['seed_facts_by_dataset']),
             note='b-t is descriptive; the reading applies the t bars to b-a on all 117 items')
    return dict(rows=out, statistics=statistics, precision_recall=precision_recall, reading=verdict,
                reproduction=dict(a_e_rows_equal=True, relift_stats_equal=True, items=len(out), captures=len({r['capture'] for r in out})),
                b=b)


GTC_FIELDS = ('rows', 'statistics', 'precision_recall', 'reading', 'reproduction')


def gtc_view(result):
    """The GTC-shaped part of a result (rows without cell b), JSON-normalised for comparison."""
    view = {k: result[k] for k in GTC_FIELDS}
    view['rows'] = [dict({k: v for k, v in r.items() if k != 'b'}, gaps={k: v for k, v in r['gaps'].items() if k != 'b'})
                    for r in result['rows']]
    return json.loads(getattr(json, '_a0_dumps', json.dumps)(view, allow_nan=False))


def assert_ts_equal(result, contract_ts, gtc_relift=G.GTC_OUT/'RELIFT_GTC.json'):
    """t and s (and a, e, the reading and reproduction) equal RELIFT_GTC.json; raises without showing any value."""
    ref = G.read_json(gtc_relift)
    if ref.get('status') != 'complete' or ref.get('track_contract_digest') != contract_ts:
        raise AssertionError('RELIFT_GTC.json is not the complete read of the same t/s tracks')
    mine = gtc_view(result)
    bad = [k for k in GTC_FIELDS if mine[k] != ref[k]]
    if bad:
        raise AssertionError('t/s outputs differ from RELIFT_GTC.json in: '+', '.join(bad))
    return True


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--tracks', type=Path, default=G.GTC_OUT/'track', help='GTC t and s tracks (read-only)')
    ap.add_argument('--tracks-b', type=Path, default=G.OUT/'track', help='GTC-B b tracks')
    ap.add_argument('--gtc-relift', type=Path, default=G.GTC_OUT/'RELIFT_GTC.json')
    ap.add_argument('--out', type=Path, default=G.OUT/'RELIFT_GTCB.json')
    args = ap.parse_args(argv)
    R = G.load_relift(); R.dependencies()
    source = track_source(args.tracks)
    source_b = track_source(args.tracks_b, G.SEEDS_B, G.B_ARMS)
    fresh = fresh_relift(R)
    result = compute(R, fresh, source, source_b)
    assert_ts_equal(result, source.contract, args.gtc_relift)
    result.update(status='complete', tracks=str(args.tracks), track_contract_digest=source.contract,
                  tracks_b=str(args.tracks_b), track_contract_digest_b=source_b.contract,
                  ts_equal_relift_gtc=dict(path=str(args.gtc_relift), sha256=G.sha256_file(args.gtc_relift), fields=list(GTC_FIELDS), equal=True),
                  definitions=dict(t='SAM 3 tracker seeded with the bound GT instance on its first visible anchor, forward over the 32 '
                                     'served anchors; deployed bestspread lift and min-area fit (relift.fit_lift).',
                                   s='SAM 3 tracker seeded with the served mask on the deployed lift best frame (K1 S_A0 rule); '
                                     'same lift and fit.',
                                   share='(k-a)/(e-a): ratio of item means; interval from the ratio of the same bootstrap draws.',
                                   seed200='items whose every operand has a t seed with status OK and area_240 >= 200 '
                                           '(SEEDS_GTC); an operand without a t seed excludes its item; t-a with the same bootstrap.',
                                   reading='registered bars on t-a over all 117 items: >= 8 with lower bound > 0 -> '
                                           'source_once_seed_right; <= 4 with upper bound < 8 -> not_the_source unless the seed200 '
                                           'subset shows t-a >= 8 with lower bound > 0 (then undecided); otherwise undecided.',
                                   precision_recall='per (item, operand, anchor) with GT or prediction nonempty; precision mean over '
                                                    'frames with prediction nonempty, recall mean over frames with GT nonempty.',
                                   b='SAM 3 tracker seeded with the bound GT instance on the anchor where its 240x320 area is largest '
                                     '(ties lowest), forward and backward over the 32 served anchors (K1 carry rule); same lift and fit; '
                                     'operands with no visible anchor keep empty masks.',
                                   b_reading='registered bars on b-a over all 117 items: >= 8 with lower bound > 0 -> '
                                             'source_when_seeded_on_best_frame; <= 4 with upper bound < 8 -> not_the_source; '
                                             'otherwise undecided (no seed-size guard). b-t is descriptive.'),
                  input_sha256={str(p): G.sha256_file(p) for p in (G.RELIFT, G.DEPTH, G.RECEIPT, G.ITEMS, G.SEEDS_TS, G.SEEDS_B,
                                                                   G.FRAMES_PATH, args.gtc_relift, Path(__file__))})
    G.write_json(args.out, result)
    print('complete')
    return 0


if __name__ == '__main__':
    sys.exit(main())
