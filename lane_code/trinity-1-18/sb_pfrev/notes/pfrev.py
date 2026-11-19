"""sb_pfrev independent recomputation: venue-381879 pose rows, BENCH v2 rule, P join, frame-pool audit.

Reads only local /scratch inputs (hash-checked); writes notes/pfrev_out.json and notes/sealed/.
"""
import ast
import collections
import gzip
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path('/scratch/jjyeung/orch_n30')
HERE = Path(__file__).resolve().parent
KIT = ROOT/'sb_records/out/kit/inputs'
TREE = ROOT/'tree_rebuild10_w/w20/work/tree_r1/student_pilot'
INPUTS = {
    'a2proj': (KIT/'84a3fab0968f2feb3524d7a14f325cb43ec2fc6c15e7af223f91234566b8f127_ap__f02f16ad__s__a2v3__rows.scenes.jsonl.gz', '84a3fab0'),
    'a3proj': (KIT/'31582e359aa30bf6c08d92773b69702642a51e3ddf3e2a7a6f64c657aaec1bb6_ap__f02f16ad__s__a3v2__rows.scenes.jsonl.gz', '31582e35'),
    'bench': (ROOT/'tree_rebuild10_w/ext/pk/benchmark_scene_exclusions.json', '3119aa4a'),
    'dev': (ROOT/'tree_rebuild10_w/w17b/work/tree_r1/student_pilot/r2_dev_merged.json', 'a1869ae2'),
    'eval_rooms': (KIT/'267efeb1ecf1c1c8329cb4b1809ed05069d9f8d0178a35caba25a9e430a4fd33_EVAL_ROOMS.json', '267efeb1'),
    'mix': (KIT/'8957d119bfa6776efe776816675da6d0f610a6e8c336acd66c297f29cf4e7e0f_8957d119.json', '8957d119'),
    'p_receipt': (KIT/'0664bb17418da379d2a8590a022d37bee0ab2e73a47bd0572b83a2c06a551615_ap__8865619b__runs__469ddece__inputs__prepare_dd26bb95f37a43789206c6e4d4cd94bd__prepared__receipt.json', '0664bb17'),
    'p_mix_order': (KIT/'d8d33340aabfe1e58d4bc81cd3b2c4919510c38c419ea9d81abe520844f6a1a9_ap__8865619b__runs__469ddece__inputs__prepare_dd26bb95f37a43789206c6e4d4cd94bd__prepared__pose_mix_order.json', 'd8d33340'),
    'p_scene_order': (KIT/'3cb1ccf5af6e75eb1b5a28bd7bfacbaf0ab9f8485a0fb55866dcd86271d1352a_ap__8865619b__runs__469ddece__inputs__prepare_dd26bb95f37a43789206c6e4d4cd94bd__prepared__pose_scene_order.json', '3cb1ccf5'),
    'fpjoin': (ROOT/'sb_framepool/out/FPJOIN.json', '67afe28c'),
    'posefam': (ROOT/'sb_posefam/out/POSEFAM.json', None),
    'recrev': (ROOT/'sb_recrev/notes/recrev_out.json', 'ba98a52d'),
    'tree_seal': (ROOT/'tree_rebuild10_w/w20/out/TREE_SEAL.json', 'c68f306c'),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


hashes = {}
for key, (path, prefix) in INPUTS.items():
    digest = sha(path)
    if prefix and not digest.startswith(prefix):
        sys.exit(f'{key} hash {digest} != {prefix}')
    hashes[key] = dict(path=str(path), sha256=digest)
load = lambda key: json.loads(Path(INPUTS[key][0]).read_bytes())

# Seal check of every sealed module this script copies or whose rule it re-implements.
seal = load('tree_seal')['files']
for name in ('s1_exclusions.py', 's1_scene_census.py', 'p3_provenance.py', 'carrier_c1_routing.py',
             'c1_pose_mix.py', 'carrier_c1_sweep.py', 'carrier_c1_run.py', 'r2_scene_bindings.py', 'r2_contract.py',
             'r1_population.py', 'r1_persisted.py'):
    digest = sha(TREE/name)
    if seal['student_pilot/'+name] != digest:
        sys.exit('seal mismatch '+name)
    hashes['tree:'+name] = digest


def mint(native, scene):
    return 'v' + hashlib.sha256(f'rung1 scene {native}/{scene}'.encode()).hexdigest()[:12]


# ---------- Independent rule (re-implemented from the documented BENCH/dev schemas) ----------
ALIAS = dict(scannet='d1', scannetpp='d2', scannetppv2='d2', arkitscenes='d3')
NATIVE = dict(d1='scannet', d2='scannetppv2', d3='arkitscenes')
bench, dev = load('bench'), load('dev')
corpora = {c.casefold() for c in bench.get('other_corpora', {})}
DS = {**ALIAS, 'd1': 'd1', 'd2': 'd2', 'd3': 'd3', 'scannet++': 'd2'}


def norm(name):
    ds, rest = name.split('/', 1)
    ds = ds.casefold()
    ds = DS.get(ds, ds if ds in corpora else None)
    if ds is None:
        raise ValueError('unknown prefix '+name)
    return ds+'/'+rest


def alias(k):
    ds, rest = k.split('/', 1)
    return ALIAS.get(ds, ds)+'/'+rest


bench_names = ({alias(k) for k in bench['scenes']} | {alias(k) for k in bench['physical_groups']}
               | {'/'.join(t) for t in bench['rung1_tokens']}
               | {f'{c}/{i}' for c, ids in bench.get('other_corpora', {}).items() for i in ids})
bench_names = {norm(n) for n in bench_names}
dev_list = [n for key in ('natives', 'rooms', 'physical_groups') for n in dev[key]]
for key in ('canonical', 'aliases'):
    for native, values in dev[key].items():
        dev_list += [native, *values]
dev_names = {norm(n) for n in dev_list}

# BENCH token alignment: scenes[i] <-> rung1_tokens[i] must be the minted token.
misaligned = [s for s, t in zip(bench['scenes'], bench['rung1_tokens'])
              if alias(s).split('/')[0] != t[0] or mint(NATIVE[t[0]], s.split('/', 1)[1]) != t[1]]
token_of_scene = {alias(s): '/'.join(t) for s, t in zip(bench['scenes'], bench['rung1_tokens'])}


def keys_of(row):
    ds = norm(row['dataset']+'/x').split('/')[0] if row.get('dataset') is not None else None
    scene = row['scene']
    keys = {norm(scene)} if '/' in scene else ({f'{ds}/{scene}'} if ds else
                                               ({'d1/'+scene} if re.fullmatch(r'scene\d+_\d+', scene) else set()))
    rooms = {m.group(1) for k in keys if (m := re.fullmatch(r'(d1/scene\d+)_\d+', k))}
    return keys | rooms


def verdict(row):
    keys = keys_of(row)
    return dict(benchmark=sorted(keys & bench_names), dev=sorted(keys & dev_names))


def rows(key):
    with gzip.open(INPUTS[key][0], 'rt') as handle:
        for line in handle:
            yield json.loads(line)


sources = {0: list(rows('a2proj')), 1: list(rows('a3proj'))}
census = {}
by_key = {0: collections.defaultdict(list), 1: collections.defaultdict(list)}
for src, population in sources.items():
    assert [r['i'] for r in population] == list(range(len(population)))
    counts = collections.Counter()
    for r in population:
        v = verdict(r)
        b, d = bool(v['benchmark']), bool(v['dev'])
        counts.update(seen=1, benchmark_matches=int(b), dev_matches=int(d), overlap_matches=int(b and d),
                      removed=int(b or d), retained=int(not (b or d)))
        for k in keys_of(r):
            by_key[src][k].append(r['i'])
    census[f'pose/{src}'] = dict(counts)

# ---------- Venue 381879 targets ----------
eval_rooms = load('eval_rooms')['alias_rooms']
venue = sorted(k.split('/')[1] for k, v in eval_rooms.items()
               if v == 'arkitscenes/venue381879' and re.fullmatch(r'\d+', k.split('/')[1]))
venue_alias_keys = sorted(k for k, v in eval_rooms.items() if v == 'arkitscenes/venue381879')
venue_tokens = {c: 'd3/'+mint('arkitscenes', c) for c in venue}
targets = []
for capture, token in venue_tokens.items():
    for src in (0, 1):
        for i in by_key[src].get(token, []):
            r = sources[src][i]
            v = verdict(r)
            member = bench['members'].get('d3/'+capture, {})
            targets.append(dict(qid=r['qid'], source=src, raw_index=i, capture='d3/'+capture, token=token,
                                bench_token_of_capture=token_of_scene.get('d3/'+capture),
                                bench_room=member.get('group'), bench_benchmarks=member.get('benchmarks'),
                                eval_room=eval_rooms.get('d3/'+capture), matched=v,
                                rule=('BENCH_v2 rung1_tokens' if token in {'/'.join(t) for t in bench['rung1_tokens']}
                                      else 'OTHER')))
venue_rows = {c: {s: len(by_key[s].get(t, [])) for s in (0, 1)} for c, t in venue_tokens.items()}

posefam = load('posefam')
pf = {(t['qid'], t['raw_index'], t['capture']) for t in posefam['targets']}
mine = {(t['qid'], t['raw_index'], t['capture']) for t in targets}
recrev = {k.split('/')[1]: v for k, v in load('recrev')['populations']['raw_a2v3']['VSI-Bench']['by_capture'].items()}

# ---------- Sealed-code cross-check (copied, seal-verified modules; ALIAS/alias_names by AST segment) ----------
pkg = HERE/'sealed/student_pilot'
pkg.mkdir(parents=True, exist_ok=True)
for name in ('s1_exclusions.py', 's1_scene_census.py', 'p3_provenance.py', 'r1_persisted.py'):
    shutil.copyfile(TREE/name, pkg/name)
routing_src = (TREE/'carrier_c1_routing.py').read_text()
tree = ast.parse(routing_src)
segments = ['import hashlib']
for node in tree.body:
    if (isinstance(node, ast.Assign) and any(getattr(t, 'id', None) in ('ALIAS', 'NATIVE') for t in node.targets)) or \
            (isinstance(node, ast.FunctionDef) and node.name in ('alias_key', 'alias_names')):
        segments.append(ast.get_source_segment(routing_src, node))
(pkg/'carrier_c1_routing.py').write_text('\n\n'.join(segments)+'\n')
(pkg/'__init__.py').write_text('')
sys.path.insert(0, str(pkg.parent))
from student_pilot.s1_exclusions import Exclusions  # noqa: E402

rule = Exclusions({'path': INPUTS['dev'][0].as_posix(), 'sha256': hashes['dev']['sha256']},
                  {'path': INPUTS['bench'][0].as_posix(), 'sha256': hashes['bench']['sha256']})
sealed_targets = {t['qid']: rule.matches(dict(dataset='d3', scene=t['token'].split('/')[1])) for t in targets}
sealed_census = {}
disagree = 0
for src, population in sources.items():
    for r in population:
        sealed = rule.matches(dict(dataset=r['dataset'], scene=r['scene']))
        v = verdict(r)
        disagree += int(sealed['benchmark'] != bool(v['benchmark']) or sealed['dev'] != bool(v['dev']))
        rule.keep(dict(dataset=r['dataset'], scene=r['scene']), f'pose/{src}')
sealed_census = rule.sources

# ---------- P (step-544) join ----------
p_receipt = load('p_receipt')
p_mix, p_scene = load('p_mix_order'), load('p_scene_order')
p_parts = p_receipt['streams']['pose']['scene_source']['sources']
p_join = dict(
    mix_rows=len(p_mix), scene_rows=len(p_scene),
    mix_source0_rows=sum(s == 0 for s, _ in p_mix), scene_source0_rows=sum(s == 0 for s, _ in p_scene),
    receipt_source0=dict(count=p_parts[0]['count'], benchmark_rows_dropped=p_parts[0].get('benchmark_rows_dropped'),
                         frame_prefix=p_parts[0].get('frame_prefix'), database=p_parts[0]['database']['sha256']),
    receipt_mix_spec=p_receipt['streams']['pose']['receipt']['sha256'],
    receipt_benchmark=p_receipt['benchmark_scene_exclusions']['sha256'],
    targets_in_mix=sorted(t['qid'] for t in targets if [t['source'], t['raw_index']] in p_mix),
    targets_in_scene=sorted(t['qid'] for t in targets if [t['source'], t['raw_index']] in p_scene))

# Projection binding: P's receipt census was computed from the real database rows at P's mix indices.
from student_pilot.s1_scene_census import fingerprint  # noqa: E402
binding = {}
for src in (0, 1):
    expected = p_receipt['scene_filter_report']['expected'][f'pose/{src}']
    indices = [i for s, i in p_mix if s == src]
    hist = collections.Counter(tuple(sorted(keys_of(sources[src][i]))) for i in indices)
    unique = set().union(*(set(k) for k in hist))
    binding[f'pose/{src}'] = dict(
        indices_sha256_equal=fingerprint(indices) == expected['population']['indices_sha256'],
        scene_ids_sha256_equal=fingerprint(sorted(hist.items())) == expected['scene_ids_sha256'],
        distinct_equal=len(unique) == expected['distinct_scene_ids'], rows_equal=len(indices) == expected['rows'],
        database=expected['population']['database']['sha256'])
p_join['projection_binding'] = binding

# ---------- Frame-pool audit: 146 captures and their room siblings ----------
fp = load('fpjoin')
room_members = collections.defaultdict(set)
for k, v in eval_rooms.items():
    room_members[v].add(k)
tokens_bench = {'/'.join(t) for t in bench['rung1_tokens']}
audit, survivors, sibling_survivors, unlisted_captures = [], [], [], []
for c in fp['captures']:
    token = norm(c['token'])
    listed = token in bench_names
    counts = {s: len(by_key[s].get(token, [])) for s in (0, 1)}
    alive = [(s, i) for s in (0, 1) for i in by_key[s].get(token, [])
             if not verdict(sources[s][i])['benchmark'] and not verdict(sources[s][i])['dev']]
    survivors += [dict(capture=c['canonical_scene'], token=token, source=s, raw_index=i, qid=sources[s][i]['qid'])
                  for s, i in alive]
    if not listed:
        unlisted_captures.append(dict(capture=c['canonical_scene'], token=token, rows=counts))
    fp_counts = {s: c['streams'].get(f'step544:pose/{n}', {}).get('raw_target', {}).get('count')
                 for s, n in ((0, 'a2v3'), (1, 'a3v2'))}
    # Room siblings: EVAL_ROOMS captures of the same room, plus ScanNet rescans _00.._09.
    room = c.get('room')
    sibs = set(room_members.get(room, ()))
    if room and room.startswith('scannet/'):
        sibs |= {f"d1/{room.split('/')[1]}_{k:02d}" for k in range(10)}
    sib_rows = {}
    for sib in sorted(sibs):
        ds, native = sib.split('/', 1)
        stoken = sib if re.fullmatch(r'v[0-9a-f]{12}', native) else ds+'/'+mint(NATIVE[ds], native)
        n = {s: len(by_key[s].get(stoken, [])) for s in (0, 1)}
        if n[0] or n[1]:
            sib_rows[sib] = dict(token=stoken, rows=n, bench_listed=stoken in bench_names)
            for s in (0, 1):
                for i in by_key[s].get(stoken, []):
                    v = verdict(sources[s][i])
                    if not v['benchmark'] and not v['dev']:
                        sibling_survivors.append(dict(sibling=sib, room=room, token=stoken, source=s, raw_index=i))
    audit.append(dict(capture=c['canonical_scene'], token=token, bench_listed=listed, rows=counts,
                      fpjoin_raw_rows=fp_counts, sibling_rows=sib_rows))
fp_total = {s: sum(a['rows'][s] for a in audit) for s in (0, 1)}
fp_mismatch = [a['capture'] for a in audit if any(a['fpjoin_raw_rows'][s] not in (None, a['rows'][s]) for s in (0, 1))]

out = dict(
    schema='sb-pfrev-v1', inputs=hashes,
    bench_alignment=dict(scenes=len(bench['scenes']), misaligned=misaligned),
    venue381879=dict(captures=venue, tokens=venue_tokens, rows=venue_rows),
    targets=targets,
    target_counts=dict(total=len(targets), by_capture=dict(collections.Counter(t['capture'] for t in targets)),
                       benchmark_hits=sum(bool(t['matched']['benchmark']) for t in targets),
                       dev_hits=sum(bool(t['matched']['dev']) for t in targets)),
    posefam_agreement=dict(equal=pf == mine, only_posefam=sorted(pf - mine), only_mine=sorted(mine - pf)),
    recrev_agreement={c: dict(count=v[0], examples=v[2], mine=sorted(t['qid'] for t in targets if t['capture'] == 'd3/'+c))
                      for c, v in recrev.items()},
    sealed_cross_check=dict(targets=sealed_targets, census=sealed_census, row_disagreements=disagree),
    independent_census=census,
    posefam_census={k: posefam['raw_scene_filter_census']['sources'][k] for k in ('pose/0', 'pose/1')},
    p_join=p_join,
    framepool=dict(captures=len(audit), bench_listed=sum(a['bench_listed'] for a in audit),
                   unlisted=unlisted_captures, pose_rows_on_captures=fp_total,
                   captures_with_pose_rows=sum(bool(a['rows'][0] or a['rows'][1]) for a in audit),
                   survivors=survivors, sibling_survivors=sibling_survivors,
                   sibling_rows_total={s: sum(v['rows'][s] for a in audit for v in a['sibling_rows'].values()) for s in (0, 1)},
                   fpjoin_count_mismatch=fp_mismatch, per_capture=audit),
)
(HERE/'pfrev_out.json').write_text(json.dumps(out, indent=1, sort_keys=True)+'\n')
summary = {k: out[k] for k in ('bench_alignment', 'venue381879', 'target_counts', 'posefam_agreement', 'independent_census',
                               'posefam_census', 'p_join')}
summary['sealed'] = dict(row_disagreements=disagree, census=sealed_census,
                         targets_all_benchmark=all(v['benchmark'] for v in sealed_targets.values()))
summary['framepool'] = {k: v for k, v in out['framepool'].items() if k != 'per_capture'}
summary['recrev'] = {c: (v['count'], len(v['mine']), set(v['examples']) <= set(v['mine'])) for c, v in out['recrev_agreement'].items()}
summary['rules'] = collections.Counter(t['rule'] for t in targets)
print(json.dumps(summary, indent=1, default=str))
