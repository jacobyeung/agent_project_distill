"""Reviewer plants: independent expected rooms, one CLI run per store, results to plant_out.json."""
import csv, hashlib, json, re, sqlite3, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = Path('/scratch/jjyeung/orch_n30/sb_auditfix')
TOOL = FIX/'store_room_audit.py'
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/tree_r1')
LISTS = FIX/'inputs/lists'
PY = '/scratch/jjyeung/envs/p1cpu/bin/python'
RUN = HERE/'plants'
RUN.mkdir(exist_ok=True)
NATIVE = dict(scannet='scannet', scannetpp='scannetppv2', scannetppv2='scannetppv2', arkitscenes='arkitscenes')
ALIAS = dict(scannet='d1', scannetpp='d2', scannetppv2='d2', arkitscenes='d3')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def mint(canonical):
    ds, scene = canonical.split('/', 1)
    return ALIAS[ds]+'/v'+hashlib.sha256(f'rung1 scene {NATIVE[ds]}/{scene}'.encode()).hexdigest()[:12]


visits = {r['video_id']: r['visit_id'] for r in csv.DictReader(open(LISTS/'authority_visits.raw'))}
venue_videos = {}
for video, visit in visits.items():
    if visit and visit != 'NA':
        venue_videos.setdefault(visit, []).append(video)


def room(canonical):
    ds, cap = canonical.split('/', 1)
    if ds == 'scannet':
        return 'scannet/'+re.fullmatch(r'(scene\d{4})_\d{2}', cap).group(1)
    if ds in ('scannetpp', 'scannetppv2'):
        return 'scannetpp/'+cap
    v = visits.get(cap)
    return 'arkitscenes/venue'+v if v and v != 'NA' else 'arkitscenes/capture'+cap


def norm(label):
    ds, cap = label.split('/', 1)
    return ('scannetpp/'+cap) if ds == 'scannetppv2' else label


r0 = open(LISTS/'bdb5d402.raw').read().split()
withheld = json.load(open(LISTS/'634820b4.raw'))['rooms']
bench = json.load(open(LISTS/'3119aa4a.raw'))['physical_groups']
dev = json.load(open(LISTS/'969cdb56.raw'))['physical_groups']
k1caps = [c for c in json.load(open(LISTS/'4d4736cf.raw'))['captures'] if c['k1_split'] == 'heldout']
k1 = [c['room'] for c in k1caps]
L = {'R0': {norm(x) for x in r0}, 'withheld-80': {norm(x) for x in withheld}, 'BENCH v2': {norm(x) for x in bench},
     'dev-S1': {norm(x) for x in dev}, 'K1': set(k1)}
union = set().union(*L.values())
amap = json.load(open(LISTS/'TIERED_ALIAS_MAP.raw'))['aliases']
auth = json.load(open(LISTS/'authority_aliases.raw'))
known = set(amap) | set(auth)


def lists_of(r):
    return sorted(n for n, s in L.items() if r in s)


# Pick real list rooms (last entries, unlike the builder's first-entry choice).
bpp = [x.split('/')[1] for x in bench if x.startswith('scannetppv2/') and mint(x) not in known]
dpp = [x.split('/')[1] for x in dev if x.startswith('scannetppv2/') and mint(x) not in known]
wsc = [x for x in withheld if x.startswith('scannet/') and mint(x+'_02') not in known][-1]
r0sc = [x for x in r0 if x.startswith('scannet/')][-1]
r0pp = [x.split('/')[1] for x in r0 if x.startswith('scannetpp/') and re.fullmatch(r'[0-9a-f]{10}', x.split('/')[1])][-1]
r0odd = [x.split('/')[1] for x in r0 if x.startswith('scannetpp/') and not re.fullmatch(r'[0-9a-f]{10}', x.split('/')[1])][0]
bvenue = [x.split('venue')[1] for x in bench if x.startswith('arkitscenes/venue')
          and all(mint('arkitscenes/'+v) not in known for v in venue_videos[x.split('venue')[1]])][-1]
dvenue = [x for x in dev if x.startswith('arkitscenes/venue')][-1].split('venue')[1]
k1_canon = {c['canonical'] for c in k1caps}
k1_sib = None
for c in k1caps:
    if c['room'].startswith('arkitscenes/venue'):
        sibs = [v for v in venue_videos[c['room'].split('venue')[1]] if 'arkitscenes/'+v not in k1_canon]
        if sibs:
            k1_sib = (c['room'], sibs[0]); break
k1pp = [c['canonical'] for c in k1caps if c['canonical'].startswith('scannetpp/')][-1]
k1sc = [c['canonical'] for c in k1caps if c['canonical'].startswith('scannet/')][-1]
k1sc_rescan = k1sc[:-2]+('07' if not k1sc.endswith('07') else '08')
literal = next(((t, e['canonical']) for t, e in sorted(amap.items())
                if not re.fullmatch(r'd[123]/v[0-9a-f]{12}', t) and room(e['canonical']) in union), None)
free_sc = next('scannet/scene%04d_00' % i for i in range(807) if 'scannet/scene%04d' % i not in union)

S = lambda **kw: dict(pool='review', question_type='plant', **kw)
hits = [  # (qid, row, expected list)
    ('H1_d2hash_ppv2witness_bench', S(qid='H1', dataset='d2', scene=mint('scannetppv2/'+bpp[-1]).split('/')[1],
                                       provenance={'canonical': 'scannetppv2/'+bpp[-1]}), 'BENCH v2'),
    ('H2_d2hash_ppwitness_gtauth_dev', S(qid='H2', dataset='d2', scene=mint('scannetpp/'+dpp[-1]).split('/')[1],
                                          gt_authority={'canonical': 'scannetpp/'+dpp[-1]}), 'dev-S1'),
    ('H3_d1hash_rescan02_groundrec_withheld', S(qid='H3', dataset='d1', scene=mint(wsc+'_02').split('/')[1],
                                                 ground_record={'canonical': wsc+'_02'}), 'withheld-80'),
    ('H4_literal_alias_key', S(qid='H4', dataset=literal[0].split('/')[0], scene=literal[0].split('/', 1)[1]),
     lists_of(room(literal[1]))[0]),
    ('H5_d1_native_rescan05_r0', S(qid='H5', dataset='d1', scene=r0sc.split('/')[1]+'_05'), 'R0'),
    ('H6_ppv2_native_r0', S(qid='H6', dataset='scannetppv2', scene=r0pp), 'R0'),
    ('H7_d3_native_k1_sibling_video', S(qid='H7', dataset='d3', scene=k1_sib[1]), 'K1'),
    ('H8_d3hash_bench_venue_video', S(qid='H8', dataset='d3', scene=mint('arkitscenes/'+venue_videos[bvenue][-1]).split('/')[1],
                                       provenance={'canonical': 'arkitscenes/'+venue_videos[bvenue][-1]}), 'BENCH v2'),
    ('H9_arkit_native_dev_venue_video', S(qid='H9', dataset='arkitscenes', scene=venue_videos[dvenue][-1]), 'dev-S1'),
    ('H10_pp_native_k1', S(qid='H10', dataset='scannetpp', scene=k1pp.split('/')[1]), 'K1'),
    ('H11_scannet_k1_other_rescan', S(qid='H11', dataset='scannet', scene=k1sc_rescan.split('/')[1]), 'K1'),
]
bench_sc = [x for x in bench if x.startswith('scannet/')][-1]
refuse = [  # each alone in its own store; expected exit 2
    ('R1_framepath_only_unmapped_d2hash', S(qid='R1', dataset='d2', scene=mint('scannetppv2/'+bpp[-2]).split('/')[1],
        student_input={'frames': [{'path': '/data/scannetpp/data/%s/dslr/resized_images/DSC00001.JPG' % bpp[-2]}]})),
    ('R2_framepath_only_no_scene', S(qid='R2', student_input={'frames': [{'path': '/data/scannet/scans/%s_00/color/0.jpg' % bench_sc.split('/')[1]}]})),
    ('R3_venue_label_as_scene', S(qid='R3', dataset='arkitscenes', scene='venue'+bvenue)),
    ('R4_dataset_case_ScanNet', S(qid='R4', dataset='ScanNet', scene=bench_sc.split('/')[1]+'_00')),
    ('R5_hash_wrong_dataset_prefix', S(qid='R5', dataset='d1', scene=mint('scannetpp/'+bpp[-3]).split('/')[1])),
    ('R6_r0_nonstandard_pp_label', S(qid='R6', dataset='scannetpp', scene=r0odd)),
    ('R7_unmapped_d3hash_bench_video', S(qid='R7', dataset='d3', scene=mint('arkitscenes/'+venue_videos[bvenue][0]).split('/')[1])),
]
r0num = r0sc.split('scene')[1]
bvideo = venue_videos[bvenue][0]
probes = [  # each alone; a safe tool must hit or refuse, never exit 0 with no hit
    ('E1_scannet_unpadded', S(qid='E1', dataset='scannet', scene='scene%d_00' % int(r0num)), 'R0'),
    ('E2_scannet_overpadded', S(qid='E2', dataset='scannet', scene='scene0%s_00' % r0num), 'R0'),
    ('E3_arkit_leading_zero', S(qid='E3', dataset='arkitscenes', scene='0'+bvideo), 'BENCH v2'),
    ('E4_nested_witness_conflict_native', S(qid='E4', dataset='scannet', scene=free_sc.split('/')[1],
        provenance={'canonical': free_sc}, ground_record={'canonical': r0sc+'_00'}), 'R0'),
    ('E5_nested_witness_conflict_hashed', S(qid='E5', dataset='d1', scene=mint(free_sc).split('/')[1],
        provenance={'canonical': free_sc}, gt_authority={'canonical': bench_sc+'_00'}), 'BENCH v2'),
    ('E6_framepath_contradicts_resolvable_scene', S(qid='E6', dataset='scannet', scene=free_sc.split('/')[1],
        student_input={'frames': [{'path': '/data/scannet/scans/%s_00/color/0.jpg' % bench_sc.split('/')[1]}]}), 'BENCH v2'),
]
for _, row, _ in hits:
    tok = ALIAS.get(row['dataset'], row['dataset'])+'/'+row['scene']
    assert row['qid'] in ('H4', 'H5', 'H6', 'H7', 'H9', 'H10', 'H11') or tok not in known, tok
for qid, row in refuse:
    if 'scene' in row and row['dataset'] in ALIAS.values():
        assert row['dataset']+'/'+row['scene'] not in known, qid


def run(label, store, extra=()):
    out = RUN/label
    cmd = [PY, '-s', '-B', str(TOOL), '--store', str(store), '--tree', str(TREE), '--lists', str(LISTS), '--out', str(out), *extra]
    p = subprocess.run(cmd, capture_output=True, text=True)
    rep = json.loads((out/'audit.json').read_text())
    rows = []
    if (out/'rows.sqlite').exists():
        with sqlite3.connect(out/'rows.sqlite') as c:
            rows = c.execute('SELECT row_id,token,scene,room,tier,hits,unresolved_reason FROM rows').fetchall()
    return dict(cmd=' '.join(cmd), rc=p.returncode, stdout=p.stdout.strip(), stderr=p.stderr.strip()[-300:],
                status=rep.get('status'), hits=rep.get('hits'), unresolved_rows=rep.get('unresolved_rows'),
                rows=[dict(zip(('qid','token','scene','room','tier','hits','reason'), r)) for r in rows])


def write_jsonl(name, rows):
    p = RUN/name
    p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    return p


def write_sqlite(name, rows):
    p = RUN/name
    with sqlite3.connect(p) as c:
        c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY, row TEXT NOT NULL)')
        c.executemany('INSERT INTO rows VALUES (?,?)', [(i, json.dumps(r)) for i, r in enumerate(rows)])
    c.close()
    return p


result = {'schema': 'sb_afrev-plants-v1', 'inputs': {str(p): sha(p) for p in
          [TOOL, Path(__file__), *[LISTS/n for n in ('manifest.json','bdb5d402.raw','634820b4.raw','3119aa4a.raw','969cdb56.raw',
           '4d4736cf.raw','TIERED_ALIAS_MAP.raw','authority_aliases.raw','authority_visits.raw')],
           *[TREE/'student_pilot'/n for n in ('r1_rooms.py','carrier_c1_routing.py','p3_provenance.py','r1_persisted.py')]]}}
expected = {row['qid']: name for _, row, name in hits}
res_hits = {}
for fmt, writer in (('jsonl', write_jsonl), ('sqlite', write_sqlite)):
    store = writer('hits.'+fmt, [row for _, row, _ in hits])
    r = run('hits_'+fmt, store)
    r['per_row'] = {x['qid']: dict(expected=expected[x['qid']], got=json.loads(x['hits']), room=x['room'], tier=x['tier'],
                                    caught=expected[x['qid']] in json.loads(x['hits'])) for x in r.pop('rows')}
    r['all_caught'] = all(v['caught'] for v in r['per_row'].values()) and len(r['per_row']) == len(hits)
    res_hits[fmt] = r
result['hits'] = res_hits
result['refuse'] = {}
for label, row in refuse:
    r = run(label, write_jsonl(label+'.jsonl', [row]))
    r['caught'] = r['rc'] == 2 and r['status'] == 'REFUSED'
    result['refuse'][label] = r
r = run('R1_allow', RUN/'R1_framepath_only_unmapped_d2hash.jsonl', ['--allow-unresolved'])
result['refuse']['R1_with_allow_unresolved'] = r
result['probes'] = {}
for label, row, want in probes:
    r = run(label, write_jsonl(label+'.jsonl', [row]))
    row_out = r['rows'][0] if r['rows'] else {}
    r['true_list'] = want
    r['caught'] = r['rc'] != 0 or want in json.loads(row_out.get('hits') or '[]')
    result['probes'][label] = r
result['picked'] = dict(bench_pp=bpp[-1], dev_pp=dpp[-1], withheld=wsc, r0_scannet=r0sc, r0_pp=r0pp, r0_odd=r0odd,
                        bench_venue=bvenue, bench_venue_videos=venue_videos[bvenue], dev_venue=dvenue, k1_sibling=k1_sib,
                        k1_pp=k1pp, k1_scannet=k1sc, literal_alias=literal, free_scannet=free_sc, bench_scannet=bench_sc)
(HERE/'plant_out.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print('hits caught:', {f: v['all_caught'] for f, v in res_hits.items()})
for f, v in res_hits.items():
    print(f, v['rc'], v['status'], {q: (x['caught'], x['got'], x['tier']) for q, x in v['per_row'].items()})
for k, v in result['refuse'].items():
    print(k, v['rc'], v['status'], v.get('caught'), [x['reason'] for x in v['rows']])
for k, v in result['probes'].items():
    print(k, 'rc', v['rc'], v['status'], 'caught', v['caught'], [(x['scene'], x['room'], x['hits'], x['reason']) for x in v['rows']])
