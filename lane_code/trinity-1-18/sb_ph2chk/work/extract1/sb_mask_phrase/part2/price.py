"""Mask phrase kit part 2, CPU pricing of the SAM 3 reruns. Written by the part 1 build; its capture and aggregate modes
need out/pool_part2 from part2/sam3_pass.py, which has not run.

    bash run.sh part2/price.py capture SHARD NSHARDS [ONLY]  kit.capture on the rerun pools, per capture -> work/part2_caps/
    bash run.sh part2/price.py aggregate                     W_exact, W_new, R_cond and part2/BARS_PART2.json -> out/part2/
    bash run.sh part2/price.py fixture CAPTURE[,CAPTURE]     plumbing check on a synthetic rerun copied from the stored cache
                                                             (no SAM 3; never a part 2 result) -> work/part2_fixture/

Pools: the raw name keeps its stored K1 pool, so P0 parity and the builder check hold unchanged; every other phrase's
pool is its rerun alone (q:<w>), and fb:<w> fills the raw name's empty frames from it. R_cond (rc:raw, rc:<w>) fills the
policy phrase's empty frames with that call's conditional-score queries, all at the call's one presence. kit.py stays
byte-identical: this module swaps kit's module-level `pools` and `families` only for the duration of one capture.
"""
import sys
sys.dont_write_bytecode = True
from gate import check, fixture_dir
if __name__ == '__main__':
    check(sys.argv[1])

import collections, contextlib, gzip, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import kit as K  # noqa: E402
import aggregate as AG  # noqa: E402
T, M, S = K.T, K.M, AG.S

PART2 = HERE/'part2'
POOL = HERE/'out'/'pool_part2'
CAPS2 = K.WORK/'part2_caps'; FIXTURE = fixture_dir(); OUT2 = K.OUT/'part2'
NEW, NEW_SHA = PART2/'NEW_PHRASES.json', PART2/'NEW_PHRASES.sha256'
BARS2, BARS2_SHA = PART2/'BARS_PART2.json', PART2/'BARS_PART2.sha256'
COND_CAP = 5
STATE, ORIG = {}, dict(pools=K.pools, families=K.families)


def frozen(path, sha_file):
    assert K.sha(path) == T.read(sha_file).decode().split()[0], f'{path.name} changed after it was frozen'
    return json.loads(T.read(path))


def merged(k1, p2):
    """Stored raw-name instances (P0) plus every other phrase's rerun instances at K1 retention; R_cond queries stay out."""
    frames = {}
    for s in range(32):
        a_all, b_all = k1['frames'][str(s)]['phrases'], p2['frames'][str(s)]['phrases']
        phrases = {}
        for n in set(a_all) | set(b_all):
            a, b = a_all.get(n), b_all.get(n)
            inst = [p for p in (a or {}).get('instances', []) if p.get('source_prompt', n) == n]
            inst += [p for p in (b or {}).get('instances', []) if p['source_prompt'] != n and p['retention'] == 'k1']
            phrases[n] = dict(presence=(a or b)['presence'], instances=inst)
        frames[str(s)] = dict(phrases=phrases)
    return dict(frames=frames)


def cond_frames(p2, name, phrase):
    """Per anchor frame: the call's R_cond queries (score >= 0.5, at most 5) as reader entries, and their signature."""
    out = []
    for s in range(32):
        rec = p2['frames'][str(s)]['phrases'].get(name) or dict(instances=[])
        ps = sorted([p for p in rec['instances'] if p['source_prompt'] == phrase and p['retention'] == 'cond'],
                    key=lambda p: -float(p['score']))[:COND_CAP]
        entries = [dict(mask=K.decode(p), score=float(p['score']), presence=float(p['source_presence']), source_prompt=phrase) for p in ps]
        out.append((entries, tuple(('cond', phrase, p.get('query'), float(p['score']), float(p['source_presence'])) for p in ps)))
    return out


def pools2(cache, name, table, offline=False):
    assert not offline, 'part 2 prices no pooled raw-plus-alias pool'
    key = id(cache)
    if STATE.get('merged_of') != key:
        STATE['merged'], STATE['merged_of'] = merged(cache, STATE['p2']), key
    out = ORIG['pools'](STATE['merged'], name, table)
    for v in ['raw']+[v for v in out if v.startswith('q:')]:
        frames, sig, call = out[v]
        cond = cond_frames(STATE['p2'], name, call)
        out['rc:'+('raw' if v == 'raw' else v[2:])] = ([frames[s] if frames[s] else cond[s][0] for s in range(32)],
                                                       tuple(sig[s] if frames[s] else cond[s][1] for s in range(32)), call)
    return out


def families2(va, vb):
    yield from ORIG['families'](va, vb)
    rc = lambda vm: {k for v, k in vm.items() if v.startswith('rc:')}  # noqa: E731
    yield {(x, y) for x in rc(va) for y in rc(vb)}


@contextlib.contextmanager
def swapped(p2):
    K.pools, K.families = pools2, families2; STATE.clear(); STATE['p2'] = p2
    try:
        yield
    finally:
        K.pools, K.families = ORIG['pools'], ORIG['families']; STATE.clear()


def capture2(c, ctx, p2, source):
    assert p2['capture'] == c['canonical']
    table2 = {n: [w for w in ws if w != n] for n, ws in p2['calls'].items()}
    with swapped(p2):
        out = K.capture(c, ctx[:5]+(table2,)+ctx[6:])
    new = json.loads(T.read(NEW))['phrases']
    for n, o in out['names'].items():
        o['in_dictionary'] = n in ctx[5]; o['new_phrases'] = [w for w in new.get(n, []) if w in table2.get(n, [])]
        o['cond_fills'] = {}
        for v in [v for v in o['variants'] if v.startswith('rc:')]:
            base = o['keys'][o['variants'][base_of(v)]]['pool_per_frame']; rc = o['keys'][o['variants'][v]]['pool_per_frame']
            o['cond_fills'][v] = sum(base[s] == 0 and rc[s] > 0 for s in range(32))
    out['part2'] = dict(source=source, calls=p2['calls'])
    return out


def base_of(rc_variant):
    return 'raw' if rc_variant == 'rc:raw' else 'q:'+rc_variant[3:]


def run_captures(shard, n, only, fixture=False):
    check('fixture-capture' if fixture else 'capture')
    for p in (PART2/'price.py', PART2/'gate.py'):
        K.pin(p)
    caps, ctx = K.setup(); frozen(NEW, NEW_SHA); frozen(BARS2, BARS2_SHA); common = dict(T.PINS)
    folder_out = FIXTURE/'caps' if fixture else CAPS2
    folder_out.mkdir(parents=True, exist_ok=True)
    todo = [c for c in sorted(caps, key=lambda c: c['canonical']) if only is None or c['canonical'] in only][shard::n]
    for c in todo:
        dest = folder_out/(K.stub(c)+'.json.gz')
        if dest.exists():
            continue
        T.PINS.clear(); T.PINS.update(common)
        if fixture:
            out = capture2(c, ctx, fixture_pool(c, ctx), dict(fixture='synthetic rerun copied from the stored cache; not a part 2 result'))
        else:
            folder = POOL/T.R.digest(c['canonical'])[:16]
            receipt = json.loads(T.read(folder/'PART2_RECEIPT.json'))
            assert receipt['candidates_sha256'] == K.sha(folder/'candidates.json')
            out = capture2(c, ctx, json.loads(T.read(folder/'candidates.json')), dict(pool=str(folder), receipt=receipt))
        out['input_sha256'] = dict(T.PINS)
        K.write_gz(dest, out)
        print(json.dumps(dict(capture=c['canonical'], seconds=round(out['seconds'], 1), refused=len(out['reader_refused']))), flush=True)


def fixture_pool(c, ctx):
    """A synthetic rerun with the pass's format, copied from the stored cache: each called phrase's stored instances as
    its K1-retention instances, and stored instances of another phrase standing in for R_cond queries in the frames where
    a phrase keeps none. It exercises the code path only; its numbers mean nothing."""
    k1 = json.loads(T.read(T.R.K1/'run_convert_2'/T.R.digest(c['canonical'])[:16]/'candidates.json'))
    new = json.loads(T.read(NEW))['phrases']; rowids = ctx[1]
    names = sorted({n for r in c['rows'] if r['id'] in rowids for n in r['operands']})
    calls = {n: [n]+K.alias_list(n, ctx[5])+new.get(n, []) for n in names}
    frames = {}
    for s in range(32):
        phrases = {}
        for n in names:
            rec = k1['frames'][str(s)]['phrases'].get(n) or dict(presence=0., instances=[])
            inst = []
            for w in calls[n]:
                own = [dict(p, source_prompt=w, retention='k1', source_presence=K.presence_of(p, rec, n))
                       for p in rec['instances'] if p.get('source_prompt', n) == w]
                if not any(float(p['score'])*p['source_presence'] >= K.FLOOR for p in own):
                    pres = own[0]['source_presence'] if own else float(rec['presence'])
                    other = [p for p in rec['instances'] if p.get('source_prompt', n) != w and float(p['score']) >= .5]
                    own += [dict(p, source_prompt=w, retention='cond', source_presence=pres) for p in other[:COND_CAP]]
                inst += own
            phrases[n] = dict(presence=float(rec['presence']), instances=inst)
        frames[str(s)] = dict(phrases=phrases)
    return dict(capture=c['canonical'], calls=calls, frames=frames, fixture=True)


def run_fixture(names):
    check('fixture')
    frozen(BARS2, BARS2_SHA)
    for p in (PART2/'price.py', PART2/'gate.py'):
        K.pin(p)
    caps, ctx = K.setup(); frozen(NEW, NEW_SHA)
    FIXTURE.mkdir(parents=True, exist_ok=True)
    summary = []
    for c in [c for c in caps if c['canonical'] in names]:
        out = capture2(c, ctx, fixture_pool(c, ctx), dict(fixture='synthetic rerun copied from the stored cache; not a part 2 result'))
        out['input_sha256'] = dict(T.PINS)
        K.write_gz(FIXTURE/(K.stub(c)+'.json.gz'), out)
        rc = {n: {k for v, k in o['variants'].items() if v.startswith('rc:')} for n, o in out['names'].items()}
        distinct = sum(o['variants'][v] != o['variants'][base_of(v)] for o in out['names'].values() for v in o['variants'] if v.startswith('rc:'))
        summary.append(dict(capture=c['canonical'], names=len(out['names']), pools=len(out['checks']), items=len(out['items']),
                            builder_parity=all(b['passed'] for b in out['builder_parity']), survival=all(x['survival'] for x in out['checks']),
                            identities=all(x['identities'] for x in out['checks']), raw_table=all(x['table'] is not False for x in out['checks']),
                            refused=len(out['reader_refused']), rc_variants=sum(len([v for v in o['variants'] if v.startswith('rc:')]) for o in out['names'].values()),
                            rc_distinct_from_base=distinct, cond_fills={n: o['cond_fills'] for n, o in out['names'].items()},
                            rc_pairs_priced=sum(all(k in rc[n] for n, k in it['keys'].items()) for it in out['items']),
                            seconds=round(out['seconds'], 1)))
    ok = all(x['builder_parity'] and x['survival'] and x['identities'] and x['raw_table'] and not x['refused'] and x['rc_distinct_from_base']
             for x in summary)
    (FIXTURE/'FIXTURE.json').write_text(json.dumps(dict(status='PASS' if ok else 'FAIL', role='CPU plumbing check of part2/price.py on a '
                                                        'synthetic rerun; not a part 2 result', captures=summary,
                                                        input_sha256=dict(T.PINS, **{str(p): K.sha(p) for p in (PART2/'price.py', PART2/'gate.py', HERE/'kit.py', NEW, BARS2)})), indent=1))
    print(json.dumps(dict(status='PASS' if ok else 'FAIL', captures=summary), indent=1))
    return ok


def policy_rows(data, arm, choice_of):
    return AG.arm_rows(data, arm, lambda d, n: choice_of(d['fold'], n))


def safe_bar(rows, a0, good_rows):
    sub = [r for r in rows if r['row_id'] in good_rows]
    s = S.contrast(sub, [a0[r['row_id']] for r in sub])
    return dict(verdict='PASS' if s['ci95'][0] > -1.0 else 'FAIL', rows=s['rows'], estimate=s['estimate'], ci95=s['ci95'])


def worth_bar(left, right, extra=None):
    c = S.contrast(left, right)
    ok = c['estimate'] >= 1.0 and c['ci95'][0] > 0 and (extra is None or extra['verdict'] == 'PASS')
    return dict(verdict='PASS' if ok else 'FAIL', estimate=c['estimate'], ci95=c['ci95'], phrase_safe=extra)


def aggregate(fixture=False):
    check('fixture-aggregate' if fixture else 'aggregate')
    K.pin(PART2/'gate.py')
    rules = frozen(BARS2, BARS2_SHA); frozen(NEW, NEW_SHA)
    caps, ctx = K.setup()
    src, out_dir = (FIXTURE/'caps', FIXTURE/'aggregate') if fixture else (CAPS2, OUT2)
    files = sorted(src.glob('*.json.gz'))
    if len(files) != 209:
        sys.exit(f'{len(files)} of 209 part 2 captures priced; aggregate waits for all')
    data = [AG.gz(p) for p in files]
    for d, p in zip(data, files):
        d['_file'] = str(p)
        assert d['k1_split'] == 'train' and all(b['passed'] for b in d['builder_parity'])
    checks = [ch for d in data for ch in d['checks']]
    refused = [x for d in data for x in d['reader_refused']]
    assert not refused and all(ch['survival'] and ch['identities'] and ch['table'] is not False for ch in checks), 'a part 2 check failed'
    a0 = json.loads(T.read(K.WORK/'A0_ROWS.json'))['rows']['A0_deployed']
    part1 = json.loads(T.read(K.OUT/'DECISION.json'))
    chosen = part1['chosen_arm']; fc = part1['fold_choices'][chosen]
    wcf = [json.loads(line) for line in T.read(K.OUT/'PER_ITEM.jsonl').decode().splitlines()]
    wcf = [r for r in wcf if r['arm'] == chosen]
    cat = {(d['capture'], n): o['keys'][o['variants']['raw']]['category'] for d in data for n, o in d['names'].items()}
    worse = {r['id']: min((cat[(d['capture'], n)] for n in r['operands']), key=AG.WORSE.index) for d in data for r in d['rows']}
    good_rows = {i for i, w in worse.items() if w == 'good'}
    assert len(good_rows) == part1['both_good_rows']
    arms = {'W_exact': policy_rows(data, 'W_exact', lambda k, n: fc[str(k)].get(n, 'raw'))}
    objs = collections.defaultdict(list)
    for d in data:
        for n, o in d['names'].items():
            objs[n].append(dict(fold=d['fold'], on_target={v: o['keys'][k]['on_target'] for v, k in o['variants'].items()},
                                cands=['q:'+w for w in o['aliases']]))
    dropped = any(d['part2']['source'].get('receipt', {}).get('new_phrases_dropped') for d in data)
    new_choice = {}
    if not dropped:
        for k in [*range(5), None]:
            key = 'all_rooms' if k is None else str(k)
            new_choice[key] = {n: AG.choose(os_, sorted({c for o in os_ for c in o['cands']}), k) for n, os_ in sorted(objs.items())}
        arms['W_new'] = policy_rows(data, 'W_new', lambda k, n: new_choice[str(k)][n][0])
    best = max(arms, key=lambda a: (AG.mra(arms[a]), a == 'W_exact'))
    best_policy = (lambda k, n: fc[str(k)].get(n, 'raw')) if best == 'W_exact' else (lambda k, n: new_choice[str(k)][n][0])
    def rc_of(k, n):
        v = best_policy(k, n)
        assert v == 'raw' or v.startswith('q:'), ('R_cond is built on single-phrase policies only', v)
        return 'rc:raw' if v == 'raw' else 'rc:'+v[2:]
    arms['R_cond'] = policy_rows(data, 'R_cond', rc_of)
    safe = {a: safe_bar(rows, a0, good_rows) for a, rows in arms.items()}
    ex = S.contrast(arms['W_exact'], wcf)
    bars = dict(exact_holds=dict(verdict='PASS' if ex['ci95'][0] > -1.0 else 'FAIL', estimate=ex['estimate'], ci95=ex['ci95']),
                new_worth=(worth_bar(arms['W_new'], arms['W_exact'], safe['W_new']) if 'W_new' in arms
                           else dict(verdict='MISSING', reason='new-phrase pass dropped at the GPU projection; counts as not passed')),
                retention_worth=dict(worth_bar(arms['R_cond'], arms[best], safe['R_cond']), base=best,
                                     adoption='needs a seal review in addition to this bar'))
    reports = {a: AG.arm_report(data, rows, a0, good_rows) for a, rows in arms.items()}
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir/'PER_ITEM_PART2.jsonl', 'w') as f:
        for rows in arms.values():
            for r in rows:
                f.write(json.dumps(T.clean(r), allow_nan=False)+'\n')
    cf = {r['row_id']: r['prediction'] for r in wcf}
    decision = dict(bars_file=dict(path=str(BARS2), sha256=K.sha(BARS2), verified_unchanged=True), new_phrases_sha256=K.sha(NEW),
                    part1_arm=chosen, w_cf_mra=AG.mra(wcf), bars=bars, best_w=best, both_good_rows=len(good_rows),
                    w_exact_rows_equal_w_cf=sum(r['prediction'] == cf[r['row_id']] for r in arms['W_exact']),
                    arms={a: {k: v for k, v in r.items() if k != 'stats'} for a, r in reports.items()},
                    new_choices={k: {n: v for n, (v, ev) in c.items() if v != 'raw'} for k, c in new_choice.items()},
                    new_evidence={k: {n: ev for n, (v, ev) in c.items()} for k, c in new_choice.items()},
                    checks=dict(pools=len(checks), survival_failed=0, identities_failed=0, reader_refused=0), rules=rules,
                    input_sha256=dict(T.PINS, **{d['_file']: K.sha(d['_file']) for d in data},
                                      **{str(p): K.sha(p) for p in (PART2/'price.py', PART2/'sam3_pass.py', HERE/'kit.py', HERE/'aggregate.py')}),
                    heldout_opened=False, devs1_opened=False)
    if fixture:
        decision = dict(FIXTURE='synthetic reruns copied from the stored cache: a CPU dry run of this aggregate; every number is meaningless', **decision)
    (out_dir/'DECISION_PART2.json').write_text(json.dumps(T.clean(decision), indent=1, allow_nan=False))
    print(json.dumps(dict({k: v['verdict'] for k, v in bars.items()}, rows={a: len(r) for a, r in arms.items()}, best_w=best,
                          fixture=fixture)))


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode in ('capture', 'fixture-capture'):
        run_captures(int(sys.argv[2]), int(sys.argv[3]), set(sys.argv[4].split(',')) if len(sys.argv) > 4 else None, mode == 'fixture-capture')
    elif mode in ('aggregate', 'fixture-aggregate'):
        aggregate(mode == 'fixture-aggregate')
    elif mode == 'fixture':
        sys.exit(0 if run_fixture(set(sys.argv[2].split(','))) else 1)
    else:
        sys.exit('mode: capture | aggregate | fixture CAPTURES | fixture-capture | fixture-aggregate')
