"""Independent recomputation for the sb_records review (no imports from sb_records code).

Populations: step-544 admitted pointing/vqa/routing/pose, raw a2v3/a3v2/r16, frame universe,
readout training scenes. Token inversion: exhaustive ScanNet (scene0000_00..scene9999_99) and
ARKit (all 8-digit zero-padded ids plus unpadded ids < 1e7); ScanNet++ from every local
candidate list. Intersections against BENCH v2 (3119aa4a) by capture token and by physical room.
"""
import gzip, hashlib, json, os, sys, time
from collections import Counter, defaultdict
from multiprocessing import Pool

SRC = '/scratch/jjyeung/orch_n30/sb_evidence/aws_sources'
KIT = '/scratch/jjyeung/orch_n30/sb_records/out/kit/inputs'
P = SRC + '/ap__8865619b__runs__469ddece__inputs__prepare_dd26bb95f37a43789206c6e4d4cd94bd'
BENCH = KIT + '/3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970_benchmark_scene_exclusions.json'
EVAL_ROOMS = KIT + '/267efeb1ecf1c1c8329cb4b1809ed05069d9f8d0178a35caba25a9e430a4fd33_EVAL_ROOMS.json'
FRAME_PLAN = KIT + '/7cc01f3655130e9d7ef2c1fd597c5cd7c1ddbcb49314a4dce7aecc040ec88cba_frame_plan.json.gz'
FRAME_MAP = KIT + '/17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3_frame_map.jsonl.gz'
ALIAS = KIT + '/7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b_TIERED_ALIAS_MAP.json'
READOUT = SRC + '/ap__e84d901c__z__eb035f92.json'
SCOPE = ('VSI-Bench', 'VSTI', 'ReVSI')
NATIVE = {'d1': 'scannet', 'd2': 'scannetppv2', 'd3': 'arkitscenes'}


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def mint(native, scene):
    return 'v' + hashlib.sha256(('rung1 scene ' + native + '/' + scene).encode()).hexdigest()[:12]


def rows(path):
    with gzip.open(path, 'rt') as f:
        out = [json.loads(l) for l in f]
    assert all(r['i'] == j for j, r in enumerate(out)), path
    return out


def arkit_chunk(args):
    lo, hi, width, targets = args
    found = {}
    pre = b'rung1 scene arkitscenes/'
    for n in range(lo, hi):
        s = str(n).zfill(width) if width else str(n)
        t = 'v' + hashlib.sha256(pre + s.encode()).hexdigest()[:12]
        if t in targets:
            found.setdefault(t, []).append(s)
    return found


def main():
    t0 = time.time()
    inputs = {}
    bench = json.load(open(BENCH)); inputs[BENCH] = sha(BENCH)
    # BENCH self-check: every listed scene re-mints to its rung1 token.
    for s, (d, tok) in zip(bench['scenes'], bench['rung1_tokens']):
        assert s.split('/')[0] == d and mint(NATIVE[d], s.split('/', 1)[1]) == tok, s
    bank_tok, bank_room, tok_scene = defaultdict(set), defaultdict(set), {}
    for s, (d, tok) in zip(bench['scenes'], bench['rung1_tokens']):
        m = bench['members'][s]
        tok_scene[(d, tok)] = s
        for b in m['benchmarks']:
            bank_tok[b].add((d, tok)); bank_room[b].add(m['group'])
    bank_sizes = {b: [len(bank_tok[b]), len(bank_room[b])] for b in SCOPE}

    pops = {}
    pt = rows(P + '__pointing__rows.scenes.jsonl.gz'); inputs['pointing_rows'] = sha(P + '__pointing__rows.scenes.jsonl.gz')
    vq = rows(P + '__vqa__rows.scenes.jsonl.gz'); inputs['vqa_rows'] = sha(P + '__vqa__rows.scenes.jsonl.gz')
    rt = rows(P + '__routing__rows.scenes.jsonl.gz'); inputs['routing_rows'] = sha(P + '__routing__rows.scenes.jsonl.gz')
    a2 = rows(SRC + '/ap__f02f16ad__s__a2v3__rows.scenes.jsonl.gz'); inputs['a2v3_rows'] = sha(SRC + '/ap__f02f16ad__s__a2v3__rows.scenes.jsonl.gz')
    a3 = rows(SRC + '/ap__f02f16ad__s__a3v2__rows.scenes.jsonl.gz'); inputs['a3v2_rows'] = sha(SRC + '/ap__f02f16ad__s__a3v2__rows.scenes.jsonl.gz')
    r16 = rows(SRC + '/ap__5e1d07a4__f__h__r16__rows.scenes.jsonl.gz')
    idx = {}
    for n in ('pointing_scene_indices', 'vqa_scene_indices', 'routing_scene_indices', 'pose_scene_order', 'pose_mix_order'):
        f = P + '__prepared__' + n + '.json'; idx[n] = json.load(open(f)); inputs[n] = sha(f)
    for n, store in (('pointing', pt), ('vqa', vq), ('routing', rt)):
        ii = idx[n + '_scene_indices']
        assert len(set(ii)) == len(ii)
        pops['m544_admitted_' + n] = [(store[j]['dataset'], store[j]['scene'], store[j]['qid']) for j in ii]
    srcs = Counter(s for s, _ in idx['pose_scene_order'])
    pose_store = {0: a2, 1: a3}
    pops['m544_admitted_pose'] = [(pose_store[s][i]['dataset'], pose_store[s][i]['scene'], pose_store[s][i]['qid'])
                                  for s, i in idx['pose_scene_order']]
    pops['raw_pointing'] = [(r['dataset'], r['scene'], r['qid']) for r in pt]
    pops['raw_vqa'] = [(r['dataset'], r['scene'], r['qid']) for r in vq]
    pops['raw_a2v3'] = [(r['dataset'], r['scene'], r['qid']) for r in a2]
    pops['raw_a3v2'] = [(r['dataset'], r['scene'], r['qid']) for r in a3]
    pops['raw_r16'] = [(r['dataset'], r['scene'], r['qid']) for r in r16]
    fm = []
    with gzip.open(FRAME_MAP, 'rt') as f:
        for l in f:
            r = json.loads(l); fm.append((r['d'], r['s'], 'frame:%s' % r['i']))
    pops['m544_frame_universe'] = fm; inputs[FRAME_MAP] = sha(FRAME_MAP)
    pops['readout_training_scenes'] = [(d, t, None) for d, t in json.load(open(READOUT))['scenes']]
    inputs[READOUT] = sha(READOUT)

    targets = defaultdict(set)
    for v in pops.values():
        for d, t, _ in v:
            targets[d].add(t)
    resolved = {}  # (d, token) -> list of (canonical, method)

    def note(d, t, canon, method):
        resolved.setdefault((d, t), set()).add((canon, method))

    # ScanNet exhaustive.
    for a in range(10000):
        for b in range(100):
            s = 'scene%04d_%02d' % (a, b); t = mint('scannet', s)
            if t in targets['d1']:
                note('d1', t, 'scannet/' + s, 'enum_scannet')
    # ARKit exhaustive (16 processes).
    tg = frozenset(targets['d3'])
    jobs = [(lo, min(lo + 2_000_000, 100_000_000), 8, tg) for lo in range(0, 100_000_000, 2_000_000)]
    jobs += [(lo, min(lo + 2_000_000, 10_000_000), 0, tg) for lo in range(0, 10_000_000, 2_000_000)]
    with Pool(16) as pool:
        for found in pool.imap_unordered(arkit_chunk, jobs):
            for t, names in found.items():
                for s in names:
                    note('d3', t, 'arkitscenes/' + s, 'enum_arkit')
    # ScanNet++ candidates from every local list; both native spellings.
    cands = set()
    for s in bench['scenes']:
        if s.startswith('d2/'):
            cands.add(s[3:])
    plan = json.load(gzip.open(FRAME_PLAN)); inputs[FRAME_PLAN] = sha(FRAME_PLAN)
    for v in plan['v'].values():
        n = v.get('n', '')
        if n.startswith('scannetpp'):
            cands.add(n.split('/', 1)[1].rsplit('.', 1)[0])
    alias = json.load(open(ALIAS)); inputs[ALIAS] = sha(ALIAS)
    for k, v in alias['aliases'].items():
        c = v.get('canonical') if isinstance(v, dict) else None
        if c and c.startswith('scannetpp'):
            cands.add(c.split('/', 1)[1])
    er = json.load(open(EVAL_ROOMS)); inputs[EVAL_ROOMS] = sha(EVAL_ROOMS)
    for k in er['alias_rooms']:
        if k.startswith('d2/'):
            cands.add(k[3:])
    for nat in ('scannetppv2', 'scannetpp'):
        for s in cands:
            t = mint(nat, s)
            if t in targets['d2']:
                note('d2', t, 'scannetpp/' + s, 'cand_' + nat)
    # Cross-dataset sanity: a token must not resolve under another dataset's code.
    unresolved = {d: sorted(t for t in ts if (d, t) not in resolved) for d, ts in targets.items()}
    ambiguous = {'%s/%s' % k: sorted(v) for k, v in resolved.items() if len({c for c, _ in v}) > 1}
    canon = {k: next(iter(v))[0] for k, v in resolved.items()}

    def room(c):
        ds, s = c.split('/', 1)
        if ds == 'scannet':
            return 'scannet/' + s[:9]
        if ds == 'arkitscenes':
            return er['arkit_rooms'].get(s, 'arkitscenes/' + s + '?NO_METADATA')
        return 'scannetpp/' + s

    report = {}
    for name, v in pops.items():
        out = dict(rows=len(v), resolved=sum(1 for d, t, _ in v if (d, t) in canon))
        caps = {(d, t) for d, t, _ in v}
        out['captures'] = len(caps); out['rooms'] = len({room(canon[c]) for c in caps if c in canon})
        for b in SCOPE:
            brooms = bank_room[b]
            cap_hits = [(d, t, q) for d, t, q in v if (d, t) in bank_tok[b]]
            room_hits = [(d, t, q) for d, t, q in v if (d, t) in canon and room(canon[(d, t)]) in brooms]
            byc = Counter(canon.get((d, t), '%s/%s' % (d, t)) for d, t, _ in room_hits)
            out[b] = dict(capture_rows=len(cap_hits), room_rows=len(room_hits),
                          by_capture={c: [n, room(c), [q for d, t, q in room_hits if canon.get((d, t)) == c][:2]]
                                      for c, n in sorted(byc.items())})
        report[name] = out
    venue = sorted(k for k, v in er['arkit_rooms'].items() if v == 'arkitscenes/venue381879')
    venue_bench = {('d3', mint('arkitscenes', s)): s for s in venue}
    venue_in = {name: {s: sum(1 for d, t, _ in v if (d, t) == k) for k, s in venue_bench.items()} for name, v in pops.items()}
    json.dump(dict(inputs=inputs, bank_sizes=bank_sizes, pose_sources=dict(srcs),
                   targets={d: len(t) for d, t in targets.items()}, resolved=len(canon),
                   unresolved=unresolved, ambiguous=ambiguous,
                   methods=Counter(m for v in resolved.values() for _, m in v),
                   venue381879_captures=venue, venue381879_rows=venue_in,
                   populations=report, seconds=round(time.time() - t0)),
              open(os.path.join(os.path.dirname(__file__), 'recrev_out.json'), 'w'), indent=1, sort_keys=True)
    json.dump({'%s/%s' % k: c for k, c in sorted(canon.items())},
              open(os.path.join(os.path.dirname(__file__), 'recrev_tokens.json'), 'w'))


if __name__ == '__main__':
    main()
