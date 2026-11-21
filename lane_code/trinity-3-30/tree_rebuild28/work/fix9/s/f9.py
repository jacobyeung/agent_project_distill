"""fix9, read-only: row-key check of the scene census against the filter, per stream.
L = rows the census lists, M = rows the filter matched (now + upstream), A = admitted rows.
Tree code is imported from the kit tree tar extracted at /tmp/a15_f9_174134/t."""
import gzip, importlib, json, sqlite3, sys, time
from collections import Counter
from pathlib import Path

hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74'); BW = hx('62656e63686d61726b'); BSE = BW + '_scene_exclusions'
D = Path('/tmp/a15_f9_174134'); TREE = D / 't'
NS = Path('/tmp/q_22c714e1'); OQ = NS / 'p' / 'q'
sys.path.insert(0, str(TREE))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned = prov.load, prov.pinned
pers = mod(PK + '.r1_persisted'); sx = mod(PK + '.s1_exclusions'); sb = mod(PK + '.r2_scene_bindings')
sp = mod(PK + '.s1_pool'); sr = mod(PK + '.s1_routing')
for m in (prov, sx, sb, sp, sr):
    assert str(Path(m.__file__).resolve()).startswith(str(TREE)), m.__file__
T0 = time.time()
RESULT = {}


def log(*a):
    print('%7.1fs' % (time.time() - T0), *a, flush=True)


def first(s, n=20):
    return sorted(s, key=str)[:n]


def check(name, L, M, A):
    a1, a2, b = L - M, L - A, (L & A) - M
    log('CHECK', name, '|L|', len(L), '|M|', len(M), '|A|', len(A), '|L&A|', len(L & A),
        '|M-L|', len(M - L), '|M-A|', len(M - A))
    log('  (a) L-M == L-A:', a1 == a2, '| |L-M|', len(a1), '|L-A|', len(a2))
    if a1 != a2:
        log('    first of (L-M)-(L-A):', first(a1 - a2)); log('    first of (L-A)-(L-M):', first(a2 - a1))
    log('  (b) (L&A)-M empty:', not b, '| |(L&A)-M|', len(b))
    if b:
        log('  LEAK first keys:', first(b))
    if M - L:
        log('  note: first of M-L:', first(M - L))
    RESULT[name] = dict(L=len(L), M=len(M), A=len(A), L_and_A=len(L & A), L_minus_M=len(a1), L_minus_A=len(a2),
                        a=a1 == a2, b=not b, M_minus_L=len(M - L), M_minus_A=len(M - A),
                        leak_keys=[list(k) if isinstance(k, tuple) else k for k in first(b, 200)])


def ivalues(database):
    with sqlite3.connect(pinned(database).as_uri() + '?mode=ro', uri=True) as c:
        values = [i for (i,) in c.execute('SELECT i FROM rows ORDER BY i')]
    return values


request = load(NS / 'r.json'); paths = request.pop('_paths')
old_result = load(OQ / 'RESULT.json')
PREPS = sorted((OQ / 'p').glob('prepare_*')); log('prepare dirs', [str(p) for p in PREPS]); PREP = PREPS[0]
with pers.scope(paths), pers.proof_scope(), pers.scope({p['sha256']: p['path'] for p in old_result['staged']}):
    cfg = load(OQ / 'c.json')
    log('cfg', OQ / 'c.json', prov.sha256(OQ / 'c.json'), '| dev list', cfg['dev_scene_exclusions']['sha256'][:12],
        '| test list', cfg[BSE]['sha256'][:12])
    rule = sx.Exclusions(cfg['dev_scene_exclusions'], cfg[BSE])
    rebuild = load(pinned(cfg['r2_scene_rebuild']))
    ref = load(pinned(cfg['scene_coverage']['reference']))
    log('census record', cfg['r2_scene_rebuild']['sha256'][:12], '| reference', cfg['scene_coverage']['reference']['sha256'][:12],
        '| exact_rebuilt_population', ref.get('exact_rebuilt_population'), '| source_map', json.dumps(cfg['scene_coverage']['source_map']))

    def listed(r, row):
        m = r.matched(r.identifiers(row))
        return bool(m['dev']), bool(m[BW])

    def census_listed(name, recount=True):
        """Census keys: population positions minus the census receipt's kept indices (rebuild_receipt).
        recount: the same rule (Exclusions.matched) over every population row, as a cross-check."""
        rec = load(pinned(rebuild['receipts'][name]))
        kept = set(load(pinned(rec['indices'])))
        pop, n = rec['scene_rebuild']['population'], rec['scene_rebuild']['population_count']
        Lc = set(range(n)) - kept
        info = dict(population=pop['sha256'][:12], population_count=n, kept=len(kept), listed=len(Lc),
                    ref_dev=ref['withheld_training_rows'][name]['rows_withheld'],
                    ref_test=ref['withheld_training_rows'][name].get(BW + '_rows_withheld'),
                    report=rec['source_scene_exclusions']['sources'][name])
        if recount:
            again, dev, test, count = set(), 0, 0, 0
            for idx, row in enumerate(sb.rows(pop)):
                count += 1
                d, t = listed(rule, row)
                dev += d; test += t
                if d or t:
                    again.add(idx)
            info.update(recount_rows=count, recount_listed=len(again), recount_equal=again == Lc, recount_dev=dev, recount_test=test)
        log('census', name, json.dumps(info))
        return Lc, pop

    # ---------------- pose
    log('== POSE')
    spec = load(pinned(cfg['streams']['pose']))
    log('preparation_output', cfg.get('preparation_output'))
    orders = sorted((OQ / 'p').glob('prepare_*/pose_mix_order.json')) + sorted((OQ / 'p').glob('*/pose_mix_order.json')) + sorted((D / 'orders').glob('*.json'))
    log('pose order files', [(str(f), prov.sha256(f)) for f in orders])
    order = load(orders[0])
    log('order rows per source', dict(Counter(k for k, _ in order)), 'total', len(order))
    sources = []
    for k, s in enumerate(spec['sources']):
        rec = load(pinned(s['receipt']))
        sources.append(dict(kind='rows', database=rec['database']))
    names = {}
    for name in ('pose_a2v3', 'pose_a3v2'):
        pop = load(pinned(rebuild['receipts'][name]))['scene_rebuild']['population']
        names[name] = [k for k, s in enumerate(sources) if s['database']['sha256'] == pop['sha256']]
    log('census name -> mix source', names)
    L = set()
    for name, ks in names.items():
        Lc, pop = census_listed(name)
        iv = ivalues(pop)
        log('  store', name, 'i column == 0..n-1:', iv == list(range(len(iv))), 'n', len(iv))
        L |= {(ks[0], iv[p]) for p in Lc}
    value = dict(kind='mix', count=len(order), order=prov.file_pin(orders[0]), sources=sources)
    rule_p = sx.Exclusions(cfg['dev_scene_exclusions'], cfg[BSE])
    key, selected, changes = sx.selection('pose', value, rule_p)
    A = {tuple(x) for x in order}
    kept = {tuple(x) for x in selected}
    M = A - kept
    up = sx.upstream({'pose': dict(kind='mix', sources=[dict(kind=s['kind'], receipt=s.get('receipt')) for s in spec['sources']])}, rule)
    log('pose filter counts (s1_exclusions.selection)', json.dumps(rule_p.sources), '| upstream reports', sorted(up))
    check('pose', L, M, A)
    for k in sorted({k for k, _ in A}):
        check('pose/%d' % k, {x for x in L if x[0] == k}, {x for x in M if x[0] == k}, {x for x in A if x[0] == k})
    json.dump(RESULT, open(D / 'f9_result.json', 'w'), indent=1)

    # ---------------- routing
    log('== ROUTING')
    legacy = load(pinned(cfg['streams']['routing']))
    rr = load(PREP / 'routing' / 'receipt.json')
    log('routing receipt', PREP / 'routing' / 'receipt.json', 'count', rr['count'], '| source', json.dumps(rr.get('source')),
        '| census pool selection', json.dumps(rebuild['pool_selection']), '| division', json.dumps(rr.get('division')),
        '| legacy division', json.dumps(legacy.get('division')))
    selection = load(pinned(rr['source']))
    policy = mod(PK + '.s1_route_policy').validate(cfg)
    pool_types = {kind for v in selection['sources'].values() if v['status'] == 'ELIGIBLE'
                  for kind, count in v['per_type'].items() if count and (
                      policy is None or cfg['route_table'].get(kind, 'direct') == 'route'
                      or v['kind'] == 'rows' and kind == 'route_planning')}
    log('pool_types', sorted(pool_types))
    try:
        from trace_format.contracts import contract_epoch
        with contract_epoch(cfg.get('contract_epoch', sr.new_contracts()), heading_plane_min=cfg.get('heading_plane_min', sr.heading_plane_min())):
            legacy_check = sr.compatibility(legacy['database'], legacy, pool_types)
    except Exception as error:
        log('compatibility inside contract_epoch failed', repr(error)[:300], '-> plain call')
        legacy_check = sr.compatibility(legacy['database'], legacy, pool_types)
    log('legacy_check', json.dumps({k: (v['disposition'], v['reason'], v['tested'], v['exact_execution_agreement']) for k, v in legacy_check.items()}))
    division = load(pinned(legacy['division']))
    train, heldout = set(division['train_scenes']), set(division['heldout_scenes'])
    Lc, pop = census_listed('camera')
    iv = ivalues(legacy['database'])
    log('  base', legacy['database']['sha256'][:12], 'census population', pop['sha256'][:12], 'i column == 0..n-1:', iv == list(range(len(iv))))
    L = {('base', iv[p]) for p in Lc}
    rule_r = sx.Exclusions(cfg['dev_scene_exclusions'], cfg[BSE])
    Ab, Mb = set(), set()
    with sqlite3.connect(pinned(legacy['database']).as_uri() + '?mode=ro', uri=True) as c:
        for i, enc in c.execute('SELECT i,row FROM rows ORDER BY i'):
            row = json.loads(enc)
            k = row['dataset'] + '/' + row['scene']
            if legacy_check[row['routing']['question_type']]['disposition'] == 'COMPATIBLE' and k in train and k not in heldout:
                Ab.add(('base', i))
                if not rule_r.keep(row, 'r16'):
                    Mb.add(('base', i))
    log('base admitted (census_rows predicate, s1_routing.py:319-325)', len(Ab), '| filter counts', json.dumps(rule_r.sources),
        '| job receipt r16', json.dumps(rr['source_scene_exclusions']['sources'].get('r16')))
    psel = load(pinned(rebuild['pool_selection']))
    pool = sp.Pool(psel['manifest'], psel['room_sets'])
    eligible = sorted(n for n, v in psel['sources'].items() if v['status'] == 'ELIGIBLE')
    used = sorted(s.split('/', 1)[1] for s in rr['source_scene_exclusions']['sources'] if s.startswith('pool/'))
    upool = rr['source_scene_exclusions'].get('upstream', {}).get('pool', {}).get('sources', {})
    log('pool selection', rebuild['pool_selection']['sha256'][:12], 'same as routing source:', rebuild['pool_selection']['sha256'] == rr['source']['sha256'],
        '| ELIGIBLE', eligible, '| routing pool sources', used, '| upstream pool sources', sorted(upool))
    Lp, Ap, Mp, bad_kept, disagree = set(), set(), set(), 0, 0
    for name, v in psel['sources'].items():
        keep = set(load(pinned(v['selection']))) if v.get('selection') else set()
        cnt = Counter()
        with gzip.open(pinned(v['source']), 'rt') as fh:
            for idx, line in enumerate(fh):
                row = json.loads(line)
                m = pool.scenes.matches(row)
                hit = any(m.values())
                disagree += int(hit != any(listed(rule, row)))
                cnt.update(rows=1, dev=int(m['dev']), test=int(m[BW]))
                key = ('pool', name, idx)
                if hit:
                    Lp.add(key)
                    bad_kept += int(idx in keep)
                if name in used:
                    Ap.add(key)
                    if hit:
                        Mp.add(key)
        log('  pool source', name, v['status'], dict(cnt), '| census report', json.dumps({k: psel['source_scene_exclusions']['sources'][name][k] for k in ('seen', 'dev_matches', BW + '_matches')}),
            '| routing upstream', json.dumps({k: upool[name][k] for k in ('seen', 'dev_matches', BW + '_matches')}) if name in upool else '-')
    log('pool: listed rows inside a selection', bad_kept, '| rows where pool rule and cfg rule disagree', disagree)
    check('routing/base', L, Mb, Ab)
    check('routing/pool', Lp, Mp, Ap)
    check('routing', L | Lp, Mb | Mp, Ab | Ap)
    json.dump(RESULT, open(D / 'f9_result.json', 'w'), indent=1)

    # ---------------- pointing, vqa
    for name in ('pointing', 'vqa'):
        log('==', name.upper())
        rp = load(PREP / name / 'receipt.json')
        upr = rp.get('source_scene_exclusions', {})
        log(name, 'stream receipt upstream', json.dumps(upr.get('sources')), '| nested', json.dumps({k: v.get('sources') for k, v in upr.get('upstream', {}).items()})[:600])
        Lc, pop = census_listed(name, recount=(name == 'pointing'))
        n = load(pinned(rebuild['receipts'][name]))['scene_rebuild']['population_count']
        A = set(range(n))
        if name == 'pointing':
            M = {idx for idx, row in enumerate(sb.rows(pop)) if any(listed(rule, row))}
        else:
            M = set()
        check(name, Lc, M, A)
    json.dump(RESULT, open(D / 'f9_result.json', 'w'), indent=1)
log('DONE')
