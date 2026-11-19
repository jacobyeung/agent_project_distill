"""Reviewer's independent admission join for the 146 frame-pool captures (step-544 and R1)."""
import collections, glob, gzip, hashlib, json
from pathlib import Path

ORCH = Path('/scratch/jjyeung/orch_n30')
AWS = ORCH / 'sb_evidence/aws_sources'
W = ORCH / 'tree_rebuild10_w'
KIT = ORCH / 'sb_records/out/kit/inputs'
HERE = Path(__file__).resolve().parent
P = 'ap__8865619b__runs__469ddece__inputs__prepare_dd26bb95f37a43789206c6e4d4cd94bd__'
INPUTS = {}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    INPUTS[str(p)] = h.hexdigest()
    return h.hexdigest()


def jload(p):
    sha(p); return json.load(open(p))


def mint(native_ds, scene):
    return 'v' + hashlib.sha256(('rung1 scene %s/%s' % (native_ds, scene)).encode()).hexdigest()[:12]


def rows(name):
    p = AWS / name; sha(p)
    with gzip.open(p, 'rt') as f:
        return [json.loads(l) for l in f]


R = {}
# 0. Checksums of every AWS extract against both sidecars.
sums = {}
for s in ['SHA256SUMS', 'SHA256SUMS.v3']:
    for line in open(AWS / s):
        a = line.split()
        if len(a) == 2: sums.setdefault(a[1], set()).add(a[0])
bad = [n for n, h in sums.items() if sha(AWS / n) not in h]
R['checksums'] = dict(files=len(sums), mismatches=bad)

# 1. BENCH v2, token rule, frame universe, and the target set derived from scratch.
bench = jload(W / 'ext/pk/benchmark_scene_exclusions.json')
DS = {'d1': 'scannet', 'd2': 'scannetppv2', 'd3': 'arkitscenes'}
CAN = {'d1': 'scannet', 'd2': 'scannetpp', 'd3': 'arkitscenes'}
btok = {}
for k in bench['members']:
    d, s = k.split('/', 1); btok[(d, mint(DS[d], s))] = k
R['bench'] = dict(sha=INPUTS[str(W / 'ext/pk/benchmark_scene_exclusions.json')], members=len(bench['members']),
                  token_rule_matches_rung1=set(btok) == {tuple(x) for x in bench['rung1_tokens']})
fm = set()
p = ORCH / 'sb_framepool/work/frame_map.jsonl.gz'; sha(p)
with gzip.open(p, 'rt') as f:
    for l in f:
        r = json.loads(l); fm.add((r['d'], r['s']))
inter = {t: btok[t] for t in fm if t in btok}
cls = collections.Counter()
T = {}
for t, nat in inter.items():
    m = bench['members'][nat]
    sti = 'STI-Bench/ReSTI' in m['benchmarks']; mc = 'MindCube' in m['benchmarks']; venue = m['group'] == 'arkitscenes/venue381879'
    cls[(tuple(sorted(m['benchmarks'])), m['group'] if venue else '')] += 1
    T[t] = dict(native=nat, canonical=CAN[nat[:2]] + '/' + nat[3:], room=m['group'], sti=sti, mc=mc, venue=venue, benchmarks=m['benchmarks'])
claimed = {l.split('\t')[0] for l in open(ORCH / 'sb_framepool/out/CAPTURES.tsv').read().splitlines()[1:]}
mytok = {'%s/%s' % t for t in T}
R['targets'] = dict(frame_universe_captures=len(fm), frame_universe_in_bench=len(inter),
                    classes=[[list(k[0]), k[1], v] for k, v in cls.items()],
                    sti=sum(v['sti'] for v in T.values()), mindcube=sum(v['mc'] for v in T.values()),
                    both=sum(v['sti'] and v['mc'] for v in T.values()), venue=sorted(v['native'] for v in T.values() if v['venue']),
                    d2_targets=sum(t[0] == 'd2' for t in T), equals_claimed_146=mytok == claimed, claimed=len(claimed))
TT = {t[1] for t in T}  # bare tokens of targets
BT = {t[1] for t in btok}
pre = json.load(open(HERE / 'rev_tokens.json'))['preimages']; sha(HERE / 'rev_tokens.json')
targ_can = {v['canonical'] for v in T.values()}
targ_rooms = {v['room'] for v in T.values()}
bench_can = {CAN[k[:2]] + '/' + k[3:] for k in bench['members']}


def room_of(c):
    ds, s = c.split('/', 1)
    return 'scannet/' + s[:9] if ds == 'scannet' else None


def audit(rs):
    out = dict(rows=len(rs), target_token=0, target_canonical=0, target_room_scannet=0, bench_token=0, bench_canonical=0, unresolved=0, field_mismatch=0, ids=[])
    for r in rs:
        t = r['scene']; c = pre.get(t)
        if c is None: out['unresolved'] += 1
        elif CAN[r['dataset']] != c.split('/')[0]: out['field_mismatch'] += 1
        if (r['dataset'], t) in T or t in TT:
            out['target_token'] += 1
            if len(out['ids']) < 5: out['ids'].append(r.get('qid'))
        if c in targ_can: out['target_canonical'] += 1
        if c and room_of(c) and room_of(c) in targ_rooms: out['target_room_scannet'] += 1
        if t in BT: out['bench_token'] += 1
        if c in bench_can: out['bench_canonical'] += 1
    return out


# 2. Step-544 receipt and pins.
rc = jload(AWS / (P + 'prepared__receipt.json')); st = rc['streams']
pins = {}
for n, key in [('pointing', 'indices'), ('routing', 'indices'), ('vqa', 'indices')]:
    pins[n] = sha(AWS / (P + 'prepared__%s_scene_indices.json' % n)) == st[n][key]['sha256']
pins['pose_order'] = sha(AWS / (P + 'prepared__pose_scene_order.json')) == st['pose']['order']['sha256']
pins['pose_mix'] = sha(AWS / (P + 'prepared__pose_mix_order.json')) == st['pose']['scene_source']['order']['sha256']
mind = jload(AWS / 'MIND_JOB_847538_REPORT.json')
src_db = {k: v['path'] for k, v in mind['scenes'].items()}
db_ok = {'pointing': mind['extract_8865619b']['inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/pointing/rows.sqlite']['sha256'] == st['pointing']['database']['sha256'],
         'routing': mind['extract_8865619b']['inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/routing/rows.sqlite']['sha256'] == st['routing']['database']['sha256'],
         'vqa': mind['extract_8865619b']['inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/vqa/rows.sqlite']['sha256'] == st['vqa']['database']['sha256'],
         'pose0_is_a2v3_b32359ce': st['pose']['sources'][0]['database']['sha256'] == mind['extract_a2v3']['sha256'],
         'pose1_is_a3v2_0b95850a': st['pose']['sources'][1]['database']['sha256'].startswith('0b95850a'),
         'a3v2_db_sha_recomputed_by_extract_job': False}
R['pins'] = dict(index_and_order_pins=pins, database_binding=db_ok, extract_sources=src_db)
cfg = jload(KIT / '78341acb36ffd03b9cec6de65effc9fafcbe8bccdc1dfb43e9da7bd88af47560_config.json')
R['run_config'] = dict(output=cfg['output'], preparation=cfg['preparation']['sha256'], bench=cfg['benchmark_scene_exclusions']['sha256'])

S = {}
for n, f in [('pointing', 'pointing'), ('routing', 'routing'), ('vqa', 'vqa'), ('a2v3', None), ('a3v2', None), ('r16', None)]:
    name = {'a2v3': 'ap__f02f16ad__s__a2v3__rows.scenes.jsonl.gz', 'a3v2': 'ap__f02f16ad__s__a3v2__rows.scenes.jsonl.gz',
            'r16': 'ap__5e1d07a4__f__h__r16__rows.scenes.jsonl.gz'}.get(n) or P + f + '__rows.scenes.jsonl.gz'
    S[n] = rows(name)
    assert [r['i'] for r in S[n]] == list(range(len(S[n]))), n

streams = {}
for n in ['pointing', 'routing', 'vqa']:
    idx = json.load(open(AWS / (P + 'prepared__%s_scene_indices.json' % n)))
    assert len(idx) == len(set(idx)) == st[n]['count']
    adm = [S[n][i] for i in idx]
    iset = set(idx)
    rest = [r for r in S[n] if r['i'] not in iset]
    streams[n] = dict(source=audit(S[n]), admitted=audit(adm), not_admitted=len(rest),
                      not_admitted_types=dict(collections.Counter(r.get('question_type', r.get('routing.question_type')) for r in rest)))
    if n == 'vqa':
        rt = cfg['route_table']
        streams[n]['alignment'] = dict(
            not_admitted_all_route=all(rt.get(r['question_type']) == 'route' for r in rest),
            admitted_any_route=sum(rt.get(r['question_type']) == 'route' for r in adm),
            receipt_routed_type_rows_dropped=st['vqa']['routed_type_rows_dropped'])
        for off in (-1, 1):
            sh = [S[n][i + off] for i in idx if 0 <= i + off < len(S[n])]
            streams[n]['alignment']['offset_%+d_route_rows_admitted' % off] = sum(rt.get(r['question_type']) == 'route' for r in sh)

# 3. Pose orders, reconciliation and alignment.
dev = jload(KIT / '969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986_dev_scene_exclusions.json')
devtok = {x.split('/', 1)[1] for v in dev['aliases'].values() for x in v if x.split('/', 1)[1].startswith('v')}
devtok |= {mint(DS[k[:2]], k[3:]) for k in dev['natives']}
mix = [tuple(x) for x in json.load(open(AWS / (P + 'prepared__pose_mix_order.json')))]
order = [tuple(x) for x in json.load(open(AWS / (P + 'prepared__pose_scene_order.json')))]
ms, os_ = set(mix), set(order)
sfr = rc['scene_filter_report']['sources']
pose = dict(mix_rows=len(mix), order_rows=len(order), order_subset_of_mix=os_ <= ms, duplicates_in_order=len(order) - len(os_),
            receipt_count=st['pose']['count'], receipt_scene_source_count=st['pose']['scene_source']['count'],
            receipt_reported_overlap_rows=st['pose']['reported_overlap_rows'], receipt_benchmark_rows_dropped=st['pose']['benchmark_rows_dropped'])
tot_bench = tot_targ = 0
for src, n in enumerate(['a2v3', 'a3v2']):
    rs = S[n]
    inmix = [r for r in rs if (src, r['i']) in ms]; kept = [r for r in rs if (src, r['i']) in os_]
    removed = [r for r in inmix if (src, r['i']) not in os_]; premix = [r for r in rs if (src, r['i']) not in ms]
    rb = sum(r['scene'] in BT for r in removed); rd = sum(r['scene'] in devtok and r['scene'] not in BT for r in removed)
    rt_ = sum(r['scene'] in TT for r in removed)
    tot_bench += rb; tot_targ += rt_
    e = dict(source=len(rs), mix=len(inmix), kept=len(kept), removed=len(removed), removed_bench=rb, removed_dev_only=rd,
             removed_neither=sum(r['scene'] not in BT and r['scene'] not in devtok for r in removed),
             kept_bench_or_dev=sum(r['scene'] in BT or r['scene'] in devtok for r in kept),
             target_source=sum(r['scene'] in TT for r in rs), target_premix=sum(r['scene'] in TT for r in premix), target_removed=rt_,
             premix_rows=len(premix), premix_bench=sum(r['scene'] in BT for r in premix),
             receipt=sfr['pose/%d' % src], kept_audit=audit(kept))
    for off in (-1, 1):
        sh = [rs[i + off] for (s_, i) in order if s_ == src and 0 <= i + off < len(rs)]
        e['offset_%+d_kept_bench' % off] = sum(r['scene'] in BT for r in sh)
    e['agrees_with_receipt'] = (e['mix'], e['kept'], e['removed'], e['removed_bench'], e['removed_dev_only']) == (
        e['receipt']['seen'], e['receipt']['retained'], e['receipt']['removed'], e['receipt']['benchmark_matches'], e['receipt']['dev_matches'])
    pose[n] = e
pose['final_bench_removed_total'] = tot_bench; pose['final_target_removed_total'] = tot_targ
streams['pose'] = pose

# 4. Camera rows, r16, upstream routing census.
cam = collections.Counter(); cam_t = 0; cam_n = 0
p = AWS / (P + 'routing__rows.camera_rows.jsonl.gz'); sha(p)
ridx = set(json.load(open(AWS / (P + 'prepared__routing_scene_indices.json'))))
with gzip.open(p, 'rt') as f:
    for l in f:
        x = json.loads(l); r = json.loads(x['row']); cam_n += 1
        cam[r['routing']['question_type']] += 1
        assert x['i'] in ridx and S['routing'][x['i']]['qid'] == r['qid'] and S['routing'][x['i']]['scene'] == r['scene']
        cam_t += r['scene'] in TT
streams['camera_rows'] = dict(rows=cam_n, types=dict(cam), target=cam_t)
up = rc['scene_filter_report']['upstream']['routing']
compat = up['expected']['r16']['population']['compatibility']
ok_types = {k for k, v in compat.items() if v['disposition'] == 'COMPATIBLE'}
r16 = S['r16']; rq = {r['qid'] for r in S['routing']}
rtyp = lambda r: r.get('routing.question_type', r.get('question_type'))
r16t = [r for r in r16 if r['scene'] in TT]
streams['r16'] = dict(rows=len(r16), compatible=sum(rtyp(r) in ok_types for r in r16),
                      compatible_bench=sum(rtyp(r) in ok_types and r['scene'] in BT for r in r16),
                      receipt=up['sources']['r16'], target=len(r16t),
                      target_compatible=sum(rtyp(r) in ok_types for r in r16t),
                      target_types_compatible=dict(collections.Counter(rtyp(r) for r in r16t if rtyp(r) in ok_types)),
                      target_types_other=dict(collections.Counter(rtyp(r) for r in r16t if rtyp(r) not in ok_types)),
                      target_qids_in_production_routing=sum(r['qid'] in rq for r in r16t))
streams['upstream_bench_matches'] = {k: v.get('benchmark_matches') for k, v in rc['scene_filter_report'].get('upstream', {}).items() if isinstance(v, dict)}

# 5. The 1,193 archived source ids.
hits = jload(ORCH / 'sb_framepool/work/verified_hits.json')['rows']
hq = {h['qid'] for h in hits}
adm_q = {}
for n in ['pointing', 'routing', 'vqa']:
    idx = json.load(open(AWS / (P + 'prepared__%s_scene_indices.json' % n))); adm_q[n] = {S[n][i]['qid'] for i in idx}
adm_q['pose'] = {S['a2v3' if s == 0 else 'a3v2'][i]['qid'] for s, i in order}
src_q = {n: {r['qid'] for r in S[n]} for n in S}
R['source_ids'] = dict(rows=len(hits), distinct=len(hq), captures=len({h['token'] for h in hits}),
                       all_on_targets=all(tuple(h['token'].split('/')) in T for h in hits),
                       admitted_matches={n: len(hq & q) for n, q in adm_q.items()},
                       any_source_store_matches={n: len(hq & q) for n, q in src_q.items()},
                       families=dict(collections.Counter(h['family'] for h in hits)),
                       qid_prefixes=dict(collections.Counter(h['qid'][:1] for h in hits)),
                       venue_hits=sum(T[tuple(h['token'].split('/'))]['venue'] for h in hits))

# 6. VSTI scene list vs the STI/ReSTI targets (capture and room level).
vsti = {k for k, m in bench['members'].items() if 'VSTI' in m['listed_by']}
vsti_rooms = {bench['members'][k]['group'] for k in vsti}
sti_t = {v['native'] for v in T.values() if v['sti']}
sti_all = {k for k, m in bench['members'].items() if 'STI-Bench/ReSTI' in m['benchmarks']}
R['vsti'] = dict(vsti_listed=len(vsti), datasets=dict(collections.Counter(k[:2] for k in vsti)), vsti_rooms=len(vsti_rooms),
                 sti_targets=len(sti_t), capture_overlap=sorted(vsti & sti_t),
                 room_overlap=sorted(vsti_rooms & {bench['members'][k]['group'] for k in sti_t}),
                 bench_sti_vs_vsti_capture_overlap=len(sti_all & vsti),
                 bench_sti_vs_vsti_room_overlap=len({bench['members'][k]['group'] for k in sti_all} & vsti_rooms))

# 7. Readout lists in the step-544 run config.
ro = {tuple(x) for x in jload(AWS / 'ap__e84d901c__z__eb035f92.json')['scenes']}
import numpy as np
z = np.load(AWS / 'ap__e84d901c__z__986ba20f.npz'); sha(AWS / 'ap__e84d901c__z__986ba20f.npz')
bank = set(zip(z['dataset_tokens'].tolist(), z['scene_tokens'].tolist()))
R['readout'] = dict(training_scenes=len(ro), training_scenes_targets=len(ro & set(T)),
                    training_scenes_venue=sorted(T[t]['native'] for t in ro & set(T) if T[t]['venue']),
                    bank_scenes=len(bank), bank_targets=len(bank & set(T)), bank_bench=sum(t[1] in BT for t in bank),
                    bank_disjoint_from_training=not (bank & ro))

# 8. R1 receipts: pins equal to step-544, and the files a row-level join would need.
r1 = {}
for p in sorted(W.glob('inputs/p_runtime/okh7/*/runs/*/inputs/*/prepared/s1_receipt.json')):
    d = jload(p); run = p.parts[-5]
    e = dict(bench=d['benchmark_scene_exclusions']['sha256'], counts={n: s['count'] for n, s in d['streams'].items()},
             pointing_same=d['streams']['pointing']['database']['sha256'] == st['pointing']['database']['sha256'] and d['streams']['pointing']['indices']['sha256'] == st['pointing']['indices']['sha256'],
             pose_same=d['streams']['pose']['order']['sha256'] == st['pose']['order']['sha256'] and [x['database']['sha256'] for x in d['streams']['pose']['sources']] == [x['database']['sha256'] for x in st['pose']['sources']],
             final_filter={k: v for k, v in d['scene_filter_report']['sources'].items() if k in ('routing', 'vqa')},
             needed={})
    for n in ['routing', 'vqa']:
        s = d['streams'][n]
        e['needed'][n] = {k: dict(path=s[k]['path'], sha256=s[k]['sha256']) for k in ('database', 'indices', 'receipt')}
    r1[run] = e
want = {v['sha256'] for e in r1.values() for n in e['needed'].values() for v in n.values()}
found = {}
for root in [W / 'inputs', W / 'ext/pk', AWS, ORCH / 'sb_framepool/work/blobs', KIT, ORCH / 'sb_alias2/in']:
    for f in root.rglob('*'):
        if f.is_file() and any(f.name.startswith(h[:8]) or h[:8] in f.name for h in want):
            found[str(f)] = sha(f)
R['R1'] = dict(runs=r1, local_files_matching_needed_prefixes=found,
               needed_present={h[:8]: h in found.values() for h in sorted(want)})

R['streams'] = streams
R['inputs'] = INPUTS
(HERE / 'rev_join.json').write_text(json.dumps(R, indent=1, default=str) + '\n')
print(json.dumps({k: v for k, v in R.items() if k != 'inputs'}, indent=1, default=str)[:30000])
