"""GTC-D step 3: cells t, s, b and d through relift.py's own fit_lift, gap, MRA and bootstrap, paired with a and e on its 117 items.

Copy of the GTC-B kit's relift_t.py. a, e, t, s and b are computed exactly as there (t and s from lever6/gtc/out/track, b from
lever6/gtcb/out/track on the bit-identical seed copy out/seeds_b/SEEDS_GTCB.json), and every one of those outputs must equal
lever6/gtcb/out/RELIFT_GTCB.json (rows without d, statistics, precision/recall, reading, reproduction, section b) and the t/s part
RELIFT_GTC.json; the checks compare and never print. Arm d (b's seed carried over the dense frames, out/track/d) goes through
the same fit_lift, round_gap(gap_value), official_mra x 100.
Population of d: the items whose capture has status OK in dense/DENSE_D.json (ScanNet and ScanNet++ when ARKit is absent);
captures of the manifest that are not OK are excluded and listed; the population label says which items the verdict is on.
Section 'd', overall (the d population) and per dataset (relift's split, plus ScanNet and ScanNet++ apart), with relift's
Bootstrap (10,000 physical-room draws, seed 20261120, item weighting): cell d; d-a; d-b (paired, the price of dense carrying by
itself); d-t (descriptive); e-a and b-a on the same items; share (d-a)/(e-a); per-frame precision/recall of d against the bound
GT instance at the 32 anchors; the registered reading.
Reading (defined before any d value exists; bars as t and b, on d-a over the d population):
  d-a >= 8 with lower bound > 0                                    -> source_when_dense;
  else d-a <= 4 with upper bound < 8, or d no better than b         -> not_the_source;   (d no better than b: mean of d-b <= 0)
  else                                                              -> undecided.
  The first bar is checked first, as registered; when it holds while d-b <= 0 the reading keeps source_when_dense and sets
  d_no_better_than_b, so the conflict is visible.
Per-frame precision/recall: over every (item, operand) and anchor where the GT instance or the prediction is nonempty;
  precision = |P&G|/|P| averaged over those frames with P nonempty; recall = |P&G|/|G| averaged over those with G nonempty.
Two units (kit_ark): the ScanNet unit (dense/DENSE_D.json, out/track) and the ARKit unit (dense_ark/DENSE_D_ARK.json,
out_ark/track). Each unit is complete when its manifest exists and every OK capture with b seeds has its d track file; an absent
or incomplete unit is reported with its reason and not read. Section 'd' reports three populations, each with the section above
(cell d, d-a beside d-b, d-t, e-a, b-a, share, per-dataset statistics, per-dataset P/R) and the registered reading applied to
that population alone, with its label: d.scannet_scannetpp (the ScanNet unit), d.arkit (the ARKit unit), and d.pooled (both
units' items together, all 117 when no capture is excluded), which exists only when both units are complete.
Usage (p1cpu): python relift_t.py            (defaults: t/s gtc/out/track, b gtcb/out/track, d gtcd/out/track on
                                             dense/DENSE_D.json and gtcd/out_ark/track on dense_ark/DENSE_D_ARK.json,
                                             out gtcd/out_ark/RELIFT_GTCD_ARK.json; prints only the status and unit states)
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
D_VERDICTS = ('source_when_dense', 'not_the_source', 'undecided')
FINE = dict(scannet='ScanNet', scannetppv2='ScanNet++', arkitscenes='ARKit')
# (population key, manifest datasets, fine datasets) of the two units; 'pooled' joins both.
UNITS = (('scannet_scannetpp', ['scannet', 'scannetpp'], ('ScanNet', 'ScanNet++')), ('arkit', ['arkit'], ('ARKit',)))
UNIT_NAMES = dict(scannet_scannetpp='ScanNet+ScanNet++', arkit='ARKit', pooled='pooled ScanNet+ScanNet+++ARKit')


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


def d_no_better_than_b(db):
    """The registered clause 'd no better than b', defined before reading: the item mean of d-b is <= 0."""
    return db['mean'] is not None and db['mean'] <= 0


def reading_d(da, db):
    """Registered GTC-D reading from d-a and d-b on the d population. Returns dict(verdict, reason, d_no_better_than_b)."""
    nb = d_no_better_than_b(db)
    if meets_first_bar(da):
        return dict(verdict='source_when_dense', reason='d-a >= 8 with lower bound > 0'
                    + ('; note: d-b <= 0 (d no better than b) also holds' if nb else ''), d_no_better_than_b=nb)
    if meets_second_bar(da) or nb:
        why = [w for w, ok in (('d-a <= 4 with upper bound < 8', meets_second_bar(da)), ('d no better than b (d-b <= 0)', nb)) if ok]
        return dict(verdict='not_the_source', reason='; '.join(why), d_no_better_than_b=nb)
    return dict(verdict='undecided', reason='d-a meets neither bar and d-b > 0', d_no_better_than_b=nb)


def dense_population(dense_path=G.DENSE_MANIFEST):
    """(captures with status OK, {capture: status} of the others, datasets) from the dense manifest."""
    m = G.read_json(dense_path)
    ok = {c['capture'] for c in m['captures'] if c['status'] == 'OK'}
    return ok, {c['capture']: c['status'] for c in m['captures'] if c['status'] != 'OK'}, list(m['datasets'])


def population_label(items_all, d_caps, not_ok, datasets):
    """Which of the 117 items the d verdict is on, in words."""
    n = sum(1 for i in items_all if i['capture'] in d_caps)
    names = {'scannet': 'ScanNet', 'scannetpp': 'ScanNet++', 'arkit': 'ARKit'}
    text = '%s items of the 117 (%d items)' % ('+'.join(names[d] for d in datasets), n)
    if 'arkit' not in datasets:
        text += '; ARKit is absent from arm d, so the verdict is on the ScanNet and ScanNet++ items only'
    if not_ok:
        text += '; excluded captures (dense source not reproduced): ' + ', '.join('%s (%s)' % kv for kv in sorted(not_ok.items()))
    return text


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


def track_source(track_dir, seeds_path=G.SEEDS_TS, arms=G.ARMS, seed_arm=None, captures=None, dense_sha=None):
    """source(arm, ctx) -> (32,240,320) tracker masks of the operand's unit; zeros when the arm has no seed.
    Requires every (arm, capture) file of the given arms under one contract on the given seeds file and all 32 anchors.
    t, s: track_source(gtc/out/track) on SEEDS_GTC; b: track_source(gtcb/out/track, SEEDS_GTCB, ('b',));
    d: track_source(gtcd/out/track, SEEDS_GTCB, ('d',), seed_arm={'d': 'b'}, captures=<dense OK captures>, dense_sha=<DENSE_D sha>):
    d carries b's seeds (unit ids and object entries of b); only the given captures are required, and every one of them must have
    its file (a missing file raises FileNotFoundError); an operand outside them has no d mask (the caller excludes its item)."""
    seed_arm = seed_arm or {}
    seeds = G.read_json(seeds_path); seeds_sha = G.sha256_file(seeds_path)
    by_obj = {(o['item_id'], o['name']): o for o in seeds['objects']}
    units, contracts = {}, set()
    for c in seeds['captures']:
        if captures is not None and c['capture'] not in captures:
            continue
        for arm in arms:
            sa = seed_arm.get(arm, arm)
            if not any(u['arm'] == sa for u in c['units']):
                continue
            path = Path(track_dir)/arm/(G.stub(c['capture'])+'.json.gz')
            if not path.exists():
                raise FileNotFoundError('missing track file '+str(path))
            d = G.read_json(path)
            if d['contract']['seeds_sha256'] != seeds_sha or d['anchors'] != 32 or d['skipped_units']:
                raise ValueError('track file not on the current seeds or not on all 32 anchors: '+str(path))
            if dense_sha is not None and d['contract'].get('dense_sha256') != dense_sha:
                raise ValueError('track file not on the current dense manifest: '+str(path))
            contracts.add(G.digest(d['contract']))
            want = {u['unit'] for u in c['units'] if u['arm'] == sa}
            if {u['unit'] for u in d['units']} != want:
                raise ValueError('track file units differ from the seeds file: '+str(path))
            for u in d['units']:
                units[(c['capture'], arm, u['unit'])] = G.unpack(u['masks'])
    if len(contracts) != 1:
        raise ValueError('track files written under %d contracts' % len(contracts))

    def source(arm, ctx):
        o = by_obj[(ctx['item_id'], ctx['name'])]; sa = seed_arm.get(arm, arm)
        if captures is not None and ctx['capture'] not in captures:
            raise KeyError('capture outside the track population: '+ctx['capture'])
        if o[sa]['status'] != 'OK':
            return np.zeros((32,)+G.GRID, bool)
        return units[(ctx['capture'], arm, o[sa]['unit'])]
    source.contract = contracts.pop()
    return source


def share(boot, rr, k):
    """(k-a)/(e-a): ratio of item means, and per bootstrap draw the ratio of the drawn means."""
    dk = [dict(r, delta=r[k]-r['a']) for r in rr]; de = [dict(r, delta=r['e']-r['a']) for r in rr]
    vk, _ = boot.samples(dk, 'delta'); ve, _ = boot.samples(de, 'delta')
    ratio = np.divide(vk, ve, out=np.full(len(vk), np.nan), where=np.isfinite(ve) & (ve != 0))
    mk = float(np.mean([r['delta'] for r in dk])) if rr else None; me = float(np.mean([r['delta'] for r in de])) if rr else None
    return boot.summarize(mk/me if me else None, ratio)


def compute(R, fresh, source, source_b, source_d=None, d_caps=frozenset(), seeds_path=G.SEEDS_TS, seeds_b_path=G.SEEDS_B,
            populations=None):
    """Rows and statistics for a, e, t, s, the seed-size subset and the registered t reading (GTC form), the section 'b' (GTC-B
    form), and, when source_d is given, cell d on the items of d_caps and the section 'd'. populations ({key: captures}, kit_ark):
    section 'd' becomes {key: section d on the rows of those captures}, each with its own reading.
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
    pr_d, pr_dc = {}, {}
    for it in items:
        iid, cap = it['item_id'], it['capture']; ref = refs[iid]
        if cap not in cache:
            cache.clear()
            with np.load(it['gt_path'], allow_pickle=False) as z:
                cache[cap] = (z['inst'].copy(), R.restore(depths[cap]))
        inst, g = cache[cap]
        served = {o['name'].strip().lower(): o for o in rows[iid]['objects']}
        in_d = source_d is not None and cap in d_caps
        pair = {k: [] for k in CELLS+('b',)+(('d',) if in_d else ())}
        for o in by_item[iid]:
            name = o['name']; target = inst == o['instance_id']; obj = served.get(name.strip().lower())
            sm = R.masks_array(obj['selected_masks']) if obj else np.zeros((32,)+G.GRID, bool)
            ctx = dict(item_id=iid, capture=cap, name=name, instance_id=o['instance_id'], target=target, served=sm)
            masks = dict(a=sm, e=target, t=np.asarray(source('t', ctx), bool), s=np.asarray(source('s', ctx), bool),
                         b=np.asarray(source_b('b', ctx), bool))
            if in_d:
                masks['d'] = np.asarray(source_d('d', ctx), bool)
                recs = G.precision_recall(masks['d'], target)
                pr_d.setdefault(fine(cap), []).extend(recs); pr_dc.setdefault(cap, []).extend(recs)
            for k in pair:
                if masks[k].shape != (32,)+G.GRID:
                    raise ValueError('mask grid differs for cell '+k)
                pair[k].append(R.fit_lift(name, masks[k], g)[0])
            for k in ('t', 's', 'b'):
                pr[(k, G.dataset(cap))] += G.precision_recall(masks[k], target)
        truth = float(ref['task']['ground_truth']); factor = R.unit_factor(ref['task']['question'])
        tseeds = [seed_obj[(iid, o['name'])]['t'] for o in by_item[iid]]
        seed200 = all(ts['status'] == 'OK' and seed_area[(cap, ts['unit'])] >= SEED_MIN_AREA for ts in tseeds)
        entry = dict(item_id=iid, capture=cap, room=ref['task']['room'], dataset=G.dataset(cap), seed200=seed200, gaps={})
        if in_d:
            entry['dataset_fine'] = fine(cap)
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
    result = dict(rows=out, statistics=statistics, precision_recall=precision_recall, reading=verdict,
                  reproduction=dict(a_e_rows_equal=True, relift_stats_equal=True, items=len(out), captures=len({r['capture'] for r in out})),
                  b=b)
    if source_d is not None and populations is None:
        result['d'] = section_d(boot, out, pr_d)
    elif source_d is not None:
        result['d'] = {}
        for key, caps in populations.items():
            rows = [r for r in out if 'd' in r and r['capture'] in caps]
            sub = {}
            for cap in sorted(caps):
                if cap in pr_dc:
                    sub.setdefault(fine(cap), []).extend(pr_dc[cap])
            result['d'][key] = section_d(boot, rows, sub)
    return result


def fine(cap):
    return FINE[cap.split('/', 1)[0]]


def section_d(boot, out, pr_d):
    """Section d on the rows that carry cell d: statistics overall and per dataset, precision/recall, reading; headline puts d-a
    beside d-b (and the share) for the whole population."""
    rows = [r for r in out if 'd' in r]
    groups = [('all', rows)]
    for ds in ('ScanNet/ScanNet++', 'ARKit'):
        rr = [r for r in rows if r['dataset'] == ds]
        if rr:
            groups.append((ds, rr))
    for ds in ('ScanNet', 'ScanNet++', 'ARKit'):
        rr = [r for r in rows if r['dataset_fine'] == ds]
        if rr and ds != 'ARKit':
            groups.append((ds, rr))
    stats = []
    for ds, rr in groups:
        stats.append(dict(dataset=ds, n=len(rr), rooms=len({r['room'] for r in rr}), cell_d=boot.metric(rr, 'd'),
                          versus={k: boot.metric([dict(r, delta=r[k.split('-')[0]]-r[k.split('-')[1]]) for r in rr], 'delta')
                                  for k in ('d-a', 'd-b', 'd-t', 'e-a', 'b-a')},
                          share_of_e_minus_a=share(boot, rr, 'd')))
    pr = {ds: G.summarize_pr(v) for ds, v in sorted(pr_d.items())}
    pr['all'] = G.summarize_pr([x for v in pr_d.values() for x in v])
    rel = [x for ds in ('ScanNet', 'ScanNet++') for x in pr_d.get(ds, [])]
    if rel:
        pr['ScanNet/ScanNet++'] = G.summarize_pr(rel)
    top = stats[0]['versus']
    return dict(statistics=stats, precision_recall=pr, reading=reading_d(top['d-a'], top['d-b']),
                headline={'d-a': top['d-a'], 'd-b': top['d-b'], 'share_of_e_minus_a': stats[0]['share_of_e_minus_a']},
                items=len(rows), captures=len({r['capture'] for r in rows}), rooms=len({r['room'] for r in rows}),
                note='d-t, e-a and b-a are descriptive; the reading applies the registered bars to d-a and the clause d-b <= 0 on the '
                     'd population (section d statistics[0])')


def unit_state(key, dense_path, tracks_dir, seeds_b_path=G.SEEDS_B):
    """One d unit: (state dict, source or None, OK captures, {capture: status} of the excluded). state.status is 'complete',
    'absent' (no manifest), 'incomplete' (an OK capture with b seeds lacks its d track file; the files are listed) or
    'no_ok_capture'. A manifest of the wrong datasets, or a track file on another dense manifest, raises."""
    want = dict((k, (ds, fn)) for k, ds, fn in UNITS)[key]
    state = dict(unit=key, dense=str(dense_path), tracks=str(tracks_dir))
    if not Path(dense_path).is_file():
        return dict(state, status='absent', reason='no dense manifest'), None, set(), {}
    d_caps, not_ok, datasets = dense_population(dense_path)
    if datasets != want[0] or any(fine(c) not in want[1] for c in set(d_caps) | set(not_ok)):
        raise ValueError('unit %s: dense manifest %s holds datasets %s' % (key, dense_path, datasets))
    dense_sha = G.sha256_file(dense_path)
    state.update(dense_sha256=dense_sha, ok_captures=len(d_caps), excluded=not_ok)
    if not d_caps:
        return dict(state, status='no_ok_capture', reason='no capture of the manifest has status OK'), None, set(), not_ok
    seeds = G.read_json(seeds_b_path)
    need = [Path(tracks_dir)/'d'/(G.stub(c['capture'])+'.json.gz') for c in seeds['captures']
            if c['capture'] in d_caps and any(u['arm'] == 'b' for u in c['units'])]
    missing = [str(p) for p in need if not p.exists()]
    if missing:
        return dict(state, status='incomplete', reason='%d of %d d track files missing' % (len(missing), len(need)),
                    missing=missing), None, set(d_caps), not_ok
    src = track_source(tracks_dir, seeds_b_path, G.D_ARMS, seed_arm={'d': 'b'}, captures=d_caps, dense_sha=dense_sha)
    return dict(state, status='complete', track_files=len(need), track_contract_digest=src.contract), src, set(d_caps), not_ok


def joined_source(units):
    """source(arm, ctx) over several complete units ({key: (source, captures)}), dispatched by the operand's capture."""
    def source(arm, ctx):
        for src, caps in units.values():
            if ctx['capture'] in caps:
                return src(arm, ctx)
        raise KeyError('capture outside every d unit: '+ctx['capture'])
    return source


def unit_label(items_all, caps, not_ok, key):
    """Which of the 117 items a population's d reading is on, in words."""
    n = sum(1 for i in items_all if i['capture'] in caps)
    text = '%s items of the 117 (%d items)' % (UNIT_NAMES[key], n)
    if key == 'scannet_scannetpp':
        text += '; ARKit is reported as its own unit (d.arkit) and pooled (d.pooled)'
    elif key == 'arkit':
        text += '; ScanNet and ScanNet++ are reported as their own unit (d.scannet_scannetpp) and pooled (d.pooled)'
    elif n == EXPECTED_ITEMS:
        text += '; all 117 items'
    else:
        text += '; not all 117 items'
    if not_ok:
        text += '; excluded captures (dense source not reproduced): ' + ', '.join('%s (%s)' % kv for kv in sorted(not_ok.items()))
    return text


EXPECTED_ITEMS = G.EXPECTED['items']
D_FIELDS = ('statistics', 'precision_recall', 'reading')


def scannet_equals_gtcd(section, contract_sn, gtcd_relift=G.OUT/'RELIFT_GTCD.json'):
    """Whether the ScanNet unit's section equals the sealed kit's RELIFT_GTCD.json section d (same d tracks); None when that
    file is absent or read other tracks. Compares without printing."""
    p = Path(gtcd_relift)
    if not p.is_file():
        return None
    ref = G.read_json(p)
    if ref.get('status') != 'complete' or ref.get('track_contract_digest_d') != contract_sn:
        return None
    norm = lambda x: json.loads(getattr(json, '_a0_dumps', json.dumps)({k: x[k] for k in D_FIELDS}, allow_nan=False))
    return norm(section) == norm(ref['d'])


GTC_FIELDS = ('rows', 'statistics', 'precision_recall', 'reading', 'reproduction')


def gtc_view(result):
    """The GTC-shaped part of a result (rows without cells b and d), JSON-normalised for comparison."""
    view = {k: result[k] for k in GTC_FIELDS}
    view['rows'] = [dict({k: v for k, v in r.items() if k not in ('b', 'd', 'dataset_fine')},
                         gaps={k: v for k, v in r['gaps'].items() if k not in ('b', 'd')}) for r in result['rows']]
    return json.loads(getattr(json, '_a0_dumps', json.dumps)(view, allow_nan=False))


GTCB_FIELDS = GTC_FIELDS+('b',)


def gtcb_view(result):
    """The GTC-B-shaped part of a result (rows without cell d), JSON-normalised for comparison."""
    view = {k: result[k] for k in GTCB_FIELDS}
    view['rows'] = [dict({k: v for k, v in r.items() if k not in ('d', 'dataset_fine')}, gaps={k: v for k, v in r['gaps'].items() if k != 'd'})
                    for r in result['rows']]
    return json.loads(getattr(json, '_a0_dumps', json.dumps)(view, allow_nan=False))


def assert_gtcb_equal(result, contract_ts, contract_b, gtcb_relift=G.RELIFT_GTCB):
    """a, e, t, s and b (rows, statistics, precision/recall, readings, reproduction, section b) equal RELIFT_GTCB.json; raises
    without showing any value."""
    ref = G.read_json(gtcb_relift)
    if ref.get('status') != 'complete' or ref.get('track_contract_digest') != contract_ts or ref.get('track_contract_digest_b') != contract_b:
        raise AssertionError('RELIFT_GTCB.json is not the complete read of the same t/s and b tracks')
    mine = gtcb_view(result)
    bad = [k for k in GTCB_FIELDS if mine[k] != ref[k]]
    if bad:
        raise AssertionError('a/e/t/s/b outputs differ from RELIFT_GTCB.json in: '+', '.join(bad))
    return True


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
    ap.add_argument('--tracks-b', type=Path, default=G.GTCB_OUT/'track', help='GTC-B b tracks (read-only)')
    ap.add_argument('--tracks-d', type=Path, default=G.OUT/'track', help='GTC-D d tracks, ScanNet unit')
    ap.add_argument('--dense', type=Path, default=G.DENSE_MANIFEST, help='dense manifest, ScanNet unit')
    ap.add_argument('--tracks-d-ark', type=Path, default=G.OUT_ARK/'track', help='GTC-D d tracks, ARKit unit')
    ap.add_argument('--dense-ark', type=Path, default=G.DENSE_ARK_MANIFEST, help='dense manifest, ARKit unit')
    ap.add_argument('--gtcd-relift', type=Path, default=G.OUT/'RELIFT_GTCD.json', help='the sealed kit\'s ScanNet-unit read')
    ap.add_argument('--gtc-relift', type=Path, default=G.GTC_OUT/'RELIFT_GTC.json')
    ap.add_argument('--gtcb-relift', type=Path, default=G.RELIFT_GTCB)
    ap.add_argument('--out', type=Path, default=G.OUT_ARK/'RELIFT_GTCD_ARK.json')
    args = ap.parse_args(argv)
    if args.tracks_d.resolve() == args.tracks_d_ark.resolve() or args.dense.resolve() == args.dense_ark.resolve():
        raise SystemExit('the two units need their own track directories and dense manifests')
    if args.out.resolve() in (args.gtcd_relift.resolve(), args.gtc_relift.resolve(), args.gtcb_relift.resolve()):
        raise SystemExit('--out would overwrite an earlier relift')
    R = G.load_relift(); R.dependencies()
    states, complete = {}, {}
    for key, dense_path, tracks_dir in (('scannet_scannetpp', args.dense, args.tracks_d), ('arkit', args.dense_ark, args.tracks_d_ark)):
        st, src, caps, not_ok = unit_state(key, dense_path, tracks_dir)
        states[key] = (st, caps, not_ok)
        if src is not None:
            complete[key] = (src, caps)
    if not complete:
        raise SystemExit('no complete d unit: ' + '; '.join('%s %s (%s)' % (k, v[0]['status'], v[0].get('reason')) for k, v in states.items()))
    source = track_source(args.tracks)
    source_b = track_source(args.tracks_b, G.SEEDS_B, G.B_ARMS)
    populations = {k: caps for k, (_, caps) in complete.items()}
    if len(complete) == 2:
        populations['pooled'] = set().union(*populations.values())
    d_caps = set().union(*populations.values())
    fresh = fresh_relift(R)
    result = compute(R, fresh, source, source_b, joined_source(complete), d_caps, populations=populations)
    assert_ts_equal(result, source.contract, args.gtc_relift)
    assert_gtcb_equal(result, source.contract, source_b.contract, args.gtcb_relift)
    refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
    items, _, _ = G.eligible(R, refs)
    in_items = {i['capture'] for i in items}
    for key in ('scannet_scannetpp', 'arkit', 'pooled'):
        if key not in result['d']:
            why = ('pooled verdict exists only when both units are complete' if key == 'pooled'
                   else 'unit %s: %s' % (states[key][0]['status'], states[key][0].get('reason')))
            result['d'][key] = dict(status='not_read', reason=why)
            continue
        caps = populations[key]
        not_ok = states[key][2] if key != 'pooled' else {**states['scannet_scannetpp'][2], **states['arkit'][2]}
        result['d'][key]['population'] = dict(label=unit_label(items, caps, not_ok, key), captures=sorted(caps & in_items),
                                              excluded=not_ok, items=result['d'][key]['items'])
        result['d'][key]['status'] = 'read'
    result['d']['units'] = {k: v[0] for k, v in states.items()}
    if 'scannet_scannetpp' in complete:
        result['d']['units']['scannet_scannetpp']['equals_relift_gtcd'] = scannet_equals_gtcd(
            result['d']['scannet_scannetpp'], complete['scannet_scannetpp'][0].contract, args.gtcd_relift)
    result.update(status='complete', tracks=str(args.tracks), track_contract_digest=source.contract,
                  tracks_b=str(args.tracks_b), track_contract_digest_b=source_b.contract,
                  tracks_d={k: str(v[0]['tracks']) for k, v in states.items()},
                  track_contract_digest_d={k: src.contract for k, (src, _) in complete.items()},
                  ts_equal_relift_gtc=dict(path=str(args.gtc_relift), sha256=G.sha256_file(args.gtc_relift), fields=list(GTC_FIELDS), equal=True),
                  aetsb_equal_relift_gtcb=dict(path=str(args.gtcb_relift), sha256=G.sha256_file(args.gtcb_relift),
                                               fields=list(GTCB_FIELDS), equal=True),
                  definitions=dict(d='SAM 3 tracker seeded with b\'s seed (the bound GT instance on its largest anchor) on that anchor\'s '
                                     'position in the dense sequence (dense.py), carried forward and backward over every dense frame, '
                                     'read out at the 32 served anchors under K1\'s carry rule; same lift and fit as a, e, t, s, b.',
                                   d_reading='registered bars on d-a over the d population: >= 8 with lower bound > 0 -> '
                                             'source_when_dense (checked first); else <= 4 with upper bound < 8, or d no better than b '
                                             '(mean d-b <= 0) -> not_the_source; otherwise undecided. d-t, e-a, b-a are descriptive.',
                                   d_population='per unit, the items whose capture has status OK in its manifest (DENSE_D.json, '
                                                'DENSE_D_ARK.json); pooled joins both and exists only when both units are complete; '
                                                'see d.<population>.population.label.',
                                   share='(k-a)/(e-a): ratio of item means; interval from the ratio of the same bootstrap draws.',
                                   precision_recall='per (item, operand, anchor) with GT or prediction nonempty; precision mean over '
                                                    'frames with prediction nonempty, recall mean over frames with GT nonempty.',
                                   other_cells='a, e, t, s, b and their sections are defined as in RELIFT_GTCB.json and equal it.'),
                  input_sha256={str(p): G.sha256_file(p) for p in (G.RELIFT, G.DEPTH, G.RECEIPT, G.ITEMS, G.SEEDS_TS, G.SEEDS_B,
                                                                   G.FRAMES_PATH, args.gtc_relift, args.gtcb_relift,
                                                                   Path(__file__))}
                               | {str(p): G.sha256_file(p) for p in (args.dense, args.dense_ark) if Path(p).is_file()})
    G.write_json(args.out, result)
    print('complete; units: ' + ', '.join('%s %s' % (k, v[0]['status']) for k, v in states.items())
          + '; pooled ' + ('read' if 'pooled' in populations else 'not read'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
