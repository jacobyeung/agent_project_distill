"""Independent re-audit of store v7 rooms (reviewer sb_alrev). Imports none of the builder's code."""
import collections, csv, hashlib, io, json, multiprocessing as mp, random, re, sqlite3, sys
from pathlib import Path

TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/tree_r1')
sys.path.insert(0, str(TREE))
from student_pilot.r1_rooms import Rooms  # N's class, w18 tree
import ast, types
_src = (TREE/'student_pilot/carrier_c1_routing.py').read_text()
_nodes = [n for n in ast.parse(_src).body if (isinstance(n, ast.FunctionDef) and n.name == 'alias_of')
          or (isinstance(n, ast.Assign) and any(getattr(t, 'id', '') in ('ALIAS', 'NATIVE') for t in n.targets))]
carrier = types.SimpleNamespace(); _ns = {'hashlib': hashlib}
exec(compile(ast.Module(body=_nodes, type_ignores=[]), 'carrier_c1_routing.py', 'exec'), _ns)
carrier.alias_of = _ns['alias_of']  # only to cross-check my mint re-implementation

OUT = Path(__file__).resolve().parent
STORE = Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
BUILD17 = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w17b/work/build17')
KIT = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/kit07ca49df_meta/m/k')
LISTS = {
    'R0': (Path('/scratch/jjyeung/n30_mirror/rows_r1/work/codeB/authority_cache/R0_ROOMS.txt'), 'bdb5d402'),
    'withheld-80': (Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/shared/WITHHELD_ROOMS_80.json'), '634820b4'),
    'BENCH v2': (KIT/'benchmark_scene_exclusions.json', '3119aa4a'),
    'dev-S1': (KIT/'dev_scene_exclusions.json', '969cdb56'),
    'K1': (Path('/scratch/jjyeung/orch_n30/sb_alias2/work/TEACHER_K1.raw'), '4d4736cf'),
}
BUILDER = Path('/scratch/jjyeung/orch_n30/sb_alias2')
HEX = re.compile(r'v[0-9a-f]{12}')
PFX = {'scannet': 'd1', 'scannetpp': 'd2', 'scannetppv2': 'd2', 'arkitscenes': 'd3'}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()


def mint(native, scene):
    return 'v' + hashlib.sha256(f'rung1 scene {native}/{scene}'.encode()).hexdigest()[:12]


def scan_arkit(args):
    lo, hi, targets = args
    base = hashlib.sha256(b'rung1 scene arkitscenes/'); hit = []
    for i in range(lo, hi):
        x = base.copy(); x.update(b'%d' % i); t = 'v' + x.hexdigest()[:12]
        if t in targets: hit.append((t, str(i)))
    return hit


def main():
    pins = {'store': sha(STORE)}
    assert pins['store'].startswith('210b2534'), pins
    for n, (p, pre) in LISTS.items():
        pins[n] = sha(p); assert pins[n].startswith(pre), (n, pins[n])
    auth = json.load(open(BUILD17/'proofs/rooms/RESULT.json'))['audit']['authority']
    R = Rooms(auth)  # verifies all five authority pins itself

    # ---- v7 rows
    rows = []
    con = sqlite3.connect(STORE.as_uri() + '?mode=ro&immutable=1', uri=True)
    for i, raw in con.execute('select i,row from rows order by i'):
        r = json.loads(raw); own = None
        for v in (r, r.get('provenance') or {}, r.get('ground_record') or {}, r.get('gt_authority') or {}):
            if v.get('canonical'): own = v['canonical']; break
        rows.append(dict(i=i, qid=r.get('qid'), ds=r.get('dataset'), scene=r.get('scene'), own=own,
                         pool=r.get('pool', 'MISSING'), fam=r.get('question_type', 'MISSING')))
    assert len(rows) == 204413
    fmt = collections.Counter((r['ds'], bool(HEX.fullmatch(r['scene'] or ''))) for r in rows)
    tokens = {r['ds'] + '/' + r['scene'] for r in rows}
    hexes = {t.split('/')[1] for t in tokens}

    # ---- my mint vs carrier alias_of
    for c in ('scannet/scene0000_00', 'scannetpp/124a6e789b', 'scannetppv2/124a6e789b', 'arkitscenes/41069021'):
        ds, s = c.split('/'); assert carrier.alias_of(c) == PFX[ds] + '/' + mint({'scannetpp': 'scannetppv2'}.get(ds, ds), s), c

    # ---- exhaustive preimages, prefix-agnostic (hex -> set of canonical)
    pre = collections.defaultdict(set)
    for a in range(10000):
        for b in range(100):
            s = f'scene{a:04d}_{b:02d}'; t = mint('scannet', s)
            if t in hexes: pre[t].add('scannet/' + s)
    step = 10 ** 8 // 64
    with mp.Pool(16) as pool:
        for hit in pool.imap_unordered(scan_arkit, [(k*step, (k+1)*step, hexes) for k in range(64)]):
            for t, s in hit: pre[t].add('arkitscenes/' + s)
    # ScanNet++: no exhaustive range (2^40); union of every id source on hand, both native spellings
    spp = set()
    w80 = json.load(open(LISTS['withheld-80'][0])); bench = json.load(open(LISTS['BENCH v2'][0]))
    dev = json.load(open(LISTS['dev-S1'][0])); k1raw = json.load(open(LISTS['K1'][0]))
    r0txt = open(LISTS['R0'][0]).read().split()
    for x in r0txt + w80['rooms'] + bench['physical_groups'] + dev['physical_groups']:
        if x.startswith('scannetpp'): spp.add(x.split('/')[1])
    spp |= {s.split('/')[1] for s in bench['scenes'] if s.startswith('d2/')}
    spp |= {s.split('/')[1] for s in dev['natives'] if s.startswith('d2/')}
    spp |= {c['canonical'].split('/')[1] for c in k1raw['captures'] if c['canonical'].startswith('scannetpp')}
    spp |= {r['own'].split('/')[1] for r in rows if r['own'] and r['own'].startswith('scannetpp')}
    own_only = set(spp)
    cand = json.load(open(BUILDER/'work/CANDIDATE_SCENES_FINAL.json'))['candidates']
    spp |= {c.split('/')[1] for c in cand if c.startswith('scannetpp')}
    alt_native = collections.Counter()
    for s in spp:
        t = mint('scannetppv2', s)
        if t in hexes: pre[t].add('scannetpp/' + s)
        if mint('scannetpp', s) in hexes: alt_native['scannetpp_native_hits'] += 1
    collisions = {t: sorted(c) for t, c in pre.items() if len(c) > 1}
    cross = sorted(t for t in tokens if pre.get(t.split('/')[1]) and
                   any(PFX[c.split('/')[0]] != t.split('/')[0] for c in pre[t.split('/')[1]]))

    # ---- builder map
    tm = json.load(open(BUILDER/'out/TIERED_ALIAS_MAP.json'))['aliases']
    norm = lambda c: c.replace('scannetppv2/', 'scannetpp/', 1) if c else c

    # ---- list room sets, my derivation (normalised through N's Rooms.room) and raw strings
    def cap_room(tok):  # 'dN/native' -> room
        p, s = tok.split('/', 1)
        return R.room({'d1': 'scannet', 'd2': 'scannetppv2', 'd3': 'arkitscenes'}[p] + '/' + s)
    def grp(g):
        return g if g.startswith('arkitscenes/') else R.room(g)
    sets = {
        'R0': set(R.r0),
        'withheld-80': {grp(g) for g in w80['rooms']},
        'BENCH v2': {grp(g) for g in bench['physical_groups']} | {cap_room(s) for s in bench['scenes']},
        'dev-S1': {grp(g) for g in dev['physical_groups']} | {cap_room(s) for s in dev['natives']}
                  | {R.room(c) for v in dev['canonical'].values() for c in v},
        'K1': set(R.k1),
    }
    raw_sets = {'R0': set(r0txt), 'withheld-80': set(w80['rooms']), 'BENCH v2': set(bench['physical_groups']),
                'dev-S1': set(dev['physical_groups']), 'K1': set(R.k1)}
    k1_from_raw = {R.room(c['canonical']) for c in k1raw['captures'] if c['k1_split'] == 'heldout'}
    bench_group_check = collections.Counter()
    for tok, m in bench['members'].items():
        bench_group_check['agree' if cap_room(tok) == grp(m['group']) else 'disagree'] += 1
    devroom = {(r.replace('d1/', 'scannet/').replace('d3/', 'arkitscenes/') if not r.startswith('d2/')
                else 'scannetpp/' + r[3:]) for r in dev['rooms']}

    # ---- reverse check: mint every capture of every list room, look for it in v7
    venue = collections.defaultdict(set)
    for vid, vis in R.visits.items():
        venue['arkitscenes/venue' + vis if vis != 'NA' else 'arkitscenes/capture' + vid].add(vid)
    def captures(room):
        ds, c = room.split('/', 1)
        if ds == 'scannet': return [('d1', mint('scannet', f'{c}_{b:02d}')) for b in range(100)]
        if ds == 'scannetpp': return [('d2', mint('scannetppv2', c)), ('d2', mint('scannetpp', c))]
        return [('d3', mint('arkitscenes', v)) for v in venue.get(room, [c.replace('capture', '')])]
    listed_tokens = set(bench['scenes']) | {a + '/' + b for a, b in bench['rung1_tokens']}
    listed_tokens |= {x for v in dev['aliases'].values() for x in v} | {x for v in w80['aliases'].values() for x in v}
    reverse = {}
    for n, s in sets.items():
        mt = {p + '/' + h for room in s for p, h in captures(room)}
        reverse[n] = dict(minted=len(mt), in_v7=len(mt & tokens), hex_in_v7_any_prefix=len({m.split('/')[1] for m in mt} & hexes),
                          v7_rows=sum(1 for r in rows if r['ds'] + '/' + r['scene'] in mt))
    direct_listed = sorted(listed_tokens & tokens)

    # ---- per-row recompute
    hits = {n: 0 for n in sets}; raw_hits = {n: 0 for n in sets}; tier_hits = collections.Counter()
    unres = []; disagree_builder = []; own_mismatch = []; k1_by_pool = collections.Counter(); per_tier = collections.Counter()
    spp_rows_in_bench = collections.Counter()
    for r in rows:
        t = r['ds'] + '/' + r['scene']; c = pre.get(r['scene'], set())
        c = {x for x in c if PFX[x.split('/')[0]] == r['ds']}
        mine = next(iter(c)) if len(c) == 1 else None
        if r['own'] and norm(r['own']) != mine: own_mismatch.append((r['i'], t, r['own'], mine))
        b = tm.get(t); tier = b['tier'] if b else None; per_tier[tier] += 1; r['tier'] = tier
        if not b or norm(b['canonical']) != mine: disagree_builder.append((r['i'], t, b and b['canonical'], mine))
        if mine is None: unres.append((r['i'], t)); r['room'] = None; continue
        room = R.room(mine); r['room'] = room; r['mine'] = mine
        for n in sets:
            if room in sets[n]: hits[n] += 1; tier_hits[(n, tier)] += 1
            if room in raw_sets[n]: raw_hits[n] += 1
        if room in sets['K1']: k1_by_pool[r['pool']] += 1
        if room in sets['BENCH v2'] or room in sets['dev-S1']: spp_rows_in_bench[room.split('/')[0]] += 1

    # ---- requested stratified sample: 2,000 rows over tiers A/B (1,000 each) plus all tier C
    rng = random.Random(20261119); by = collections.defaultdict(list)
    for r in rows: by[r['tier']].append(r)
    sample = rng.sample(by['A'], 1000) + rng.sample(by['B'], 1000) + by['C']
    s_ok = sum(1 for r in sample if r.get('mine') and norm(tm[r['ds'] + '/' + r['scene']]['canonical']) == r['mine'])
    s_hits = {n: sum(1 for r in sample if r['room'] in sets[n]) for n in sets}

    res = dict(pins=pins, row_formats={f'{a}:{"hash12" if b else "other"}': v for (a, b), v in fmt.items()},
               distinct_tokens=len(tokens), preimage_resolved_tokens=sum(1 for t in tokens if pre.get(t.split('/')[1])),
               scannetpp_candidates=len(spp), scannetpp_candidates_without_builder=len(own_only),
               scannetpp_native_spelling_hits=alt_native['scannetpp_native_hits'],
               collisions=collisions, cross_prefix_tokens=cross[:20], cross_prefix_count=len(cross),
               rows_unresolved=len(unres), unresolved_examples=unres[:20],
               rows_disagreeing_with_builder=len(disagree_builder), disagree_examples=disagree_builder[:20],
               own_field_vs_preimage_mismatch=len(own_mismatch), own_mismatch_examples=own_mismatch[:20],
               builder_tier_rows=dict((str(k), v) for k, v in per_tier.items()),
               list_rooms={n: len(s) for n, s in sets.items()}, raw_list_rooms={n: len(s) for n, s in raw_sets.items()},
               raw_vs_normalised_only={n: sorted(sets[n] - raw_sets[n])[:5] for n in sets},
               raw_minus_normalised={n: len(raw_sets[n] - sets[n]) for n in sets},
               k1_raw_equals_split=k1_from_raw == sets['K1'], bench_member_group_check=dict(bench_group_check),
               dev_rooms_field_equals_pg=devroom == {grp(g) for g in dev['physical_groups']},
               hits_normalised=hits, hits_raw_strings=raw_hits,
               hits_by_tier={f'{n}|{t}': v for (n, t), v in sorted(tier_hits.items(), key=str)},
               k1_by_pool=dict(k1_by_pool), reverse_mint_check=reverse, listed_tokens=len(listed_tokens),
               listed_tokens_in_v7=direct_listed[:20], listed_tokens_in_v7_count=len(direct_listed),
               sample=dict(rows=len(sample), tierA=1000, tierB=1000, tierC=len(by['C']), agree_with_builder=s_ok, hits=s_hits),
               rooms_hit_dataset=dict(spp_rows_in_bench))
    (OUT/'review_out.json').write_text(json.dumps(res, indent=1, sort_keys=True) + '\n')
    print(json.dumps(res, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
