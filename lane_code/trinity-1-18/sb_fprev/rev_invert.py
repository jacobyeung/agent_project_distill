"""Reviewer's independent token census and exhaustive inversion (ScanNet 1M, ARKit 100M, ScanNet++ candidates)."""
import collections, glob, gzip, hashlib, json, re, sys
import multiprocessing as mp
from pathlib import Path

ORCH = Path('/scratch/jjyeung/orch_n30')
AWS = ORCH / 'sb_evidence/aws_sources'
OUT = Path(__file__).resolve().parent / 'rev_tokens.json'
TOK = re.compile(r'^v[0-9a-f]{12}$')
DS = {'d1': 'scannet', 'd2': 'scannetppv2', 'd3': 'arkitscenes'}


def mint(native_ds, scene):
    return 'v' + hashlib.sha256(('rung1 scene %s/%s' % (native_ds, scene)).encode()).hexdigest()[:12]


def arkit_range(args):
    lo, hi, targets = args
    base = hashlib.sha256(b'rung1 scene arkitscenes/')
    out = []
    for i in range(lo, hi):
        h = base.copy(); h.update(str(i).encode())
        t = 'v' + h.hexdigest()[:12]
        if t in targets:
            out.append((t, 'arkitscenes/%d' % i))
    return out


def main():
    tokens = collections.Counter()
    fmt = collections.Counter()
    by_field = collections.defaultdict(set)
    for p in sorted(AWS.glob('*scenes.jsonl.gz')):
        with gzip.open(p, 'rt') as f:
            for line in f:
                r = json.loads(line)
                s = r.get('scene'); d = r.get('dataset')
                fmt[(p.name.split('__')[-2] if '__prepare' in p.name else p.name.split('__')[3], d, bool(TOK.match(str(s))))] += 1
                by_field[s].add(d)
                tokens[s] += 1
    fm = set()
    with gzip.open(ORCH / 'sb_framepool/work/frame_map.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line); fm.add((r['d'], r['s']))
    for d, s in fm:
        by_field[s].add(d)
    ro = json.load(open(AWS / 'ap__e84d901c__z__eb035f92.json'))['scenes']
    for d, s in ro:
        by_field[s].add(d)
    all_tok = {t for t in by_field if TOK.match(str(t))}
    pre = collections.defaultdict(set)
    for a in range(10000):
        for b in range(100):
            s = 'scene%04d_%02d' % (a, b); t = mint('scannet', s)
            if t in all_tok: pre[t].add('scannet/' + s)
    chunks = [(i * 6250000, (i + 1) * 6250000, all_tok) for i in range(16)]
    with mp.Pool(16) as pool:
        for hits in pool.imap_unordered(arkit_range, chunks):
            for t, c in hits: pre[t].add(c)
    # ScanNet++ candidate natives from three sources; each accepted only if it remints to the token.
    cands = set()
    bench = json.load(open(ORCH / 'tree_rebuild10_w/ext/pk/benchmark_scene_exclusions.json'))
    cands |= {k.split('/', 1)[1] for k in bench['members'] if k.startswith('d2/')}
    plan = json.load(gzip.open(ORCH / 'sb_framepool/work/frame_plan.json.gz', 'rt'))
    for v in plan['v'].values():
        n = v.get('n', '')
        if n.startswith('scannetpp/'): cands.add(n.split('/', 1)[1].rsplit('.', 1)[0])
    ti = json.load(open(ORCH / 'sb_records/out/TOKEN_INVERSION.json'))['aliases']
    cands |= {v['canonical'].split('/', 1)[1] for v in ti.values() if v['canonical'].startswith('scannetpp/')}
    for c in cands:
        t = mint('scannetppv2', c)
        if t in all_tok: pre[t].add('scannetpp/' + c)
    unresolved = sorted(all_tok - set(pre))
    unres_fields = collections.Counter(tuple(sorted(by_field[t])) for t in unresolved)
    nontoken = sorted(str(t) for t in by_field if not TOK.match(str(t)))
    out = dict(command='/usr/bin/python3 rev_invert.py', total_tokens=len(all_tok), resolved=len(pre),
               unresolved=len(unresolved), unresolved_by_dataset_field=[[list(k), v] for k, v in unres_fields.items()],
               nontoken_scene_values=nontoken[:50], nontoken_count=len(nontoken),
               collisions={t: sorted(v) for t, v in pre.items() if len(v) > 1},
               field_mismatch=sorted(t for t, v in pre.items() if len(v) == 1 and
                                    {'scannet': 'd1', 'scannetpp': 'd2', 'arkitscenes': 'd3'}[next(iter(v)).split('/')[0]] not in by_field[t]),
               scene_format=[[list(k), v] for k, v in sorted(fmt.items())],
               scannetpp_candidates=len(cands),
               preimages={t: sorted(v)[0] for t, v in pre.items() if len(v) == 1},
               unresolved_tokens=unresolved)
    OUT.write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps({k: v for k, v in out.items() if k not in ('preimages', 'unresolved_tokens')}, indent=1))


if __name__ == '__main__':
    main()
