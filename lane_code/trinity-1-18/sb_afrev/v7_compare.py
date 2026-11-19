"""Compare the reviewer's v7 rerun with sb_alias2, sb_alrev token rooms, the builder's rows, and the raw store."""
import csv, hashlib, json, re, sqlite3
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
O = Path('/scratch/jjyeung/orch_n30')
LISTS = O/'sb_auditfix/inputs/lists'
STORE = Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
NAMES = ('R0', 'withheld-80', 'BENCH v2', 'dev-S1', 'K1')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def ro(p):
    return sqlite3.connect(Path(p).as_uri()+'?mode=ro&immutable=1', uri=True)


mine = json.load(open(HERE/'v7_rerun/audit.json'))
ref = json.load(open(O/'sb_alias2/out/ROOM_AUDIT_TIERED.json'))
tok = json.load(open(O/'sb_alrev/token_rooms.json'))
nz = lambda d: {k: v for k, v in d.items() if v}
out = {'inputs': {str(p): sha(p) for p in [HERE/'v7_rerun/audit.json', HERE/'v7_rerun/rows.sqlite', O/'sb_alias2/out/ROOM_AUDIT_TIERED.json',
               O/'sb_alrev/token_rooms.json', O/'sb_auditfix/out/v7/rows.sqlite', Path(__file__), STORE]}}
cmp = {}
for key in ('hits', 'hits_by_tier', 'hits_by_stream', 'hits_by_family'):
    a = {n: (mine[key][n] if key == 'hits' else nz(mine[key][n])) for n in NAMES}
    b = {n: (ref[key][n] if key == 'hits' else nz(ref[key][n])) for n in NAMES}
    cmp[key] = {n: a[n] == b[n] for n in NAMES}
J = lambda rows: Counter({(r['list'], r['tier'], r['stream'], r['family']): r['rows'] for r in rows})
cmp['joint_equal'] = J(mine['hits_by_list_tier_stream_family']) == J(ref['hits_by_list_tier_stream_family'])
cmp['coverage_equal'] = mine['coverage_by_tier'] == {t: v['rows'] for t, v in ref['room_resolved_coverage'].items()}
cmp['rooms_resolved'] = [mine['rooms_resolved'], ref['rooms_resolved']]
cmp['k1_tiers'] = mine['hits_by_tier']['K1']
out['vs_sb_alias2'] = cmp

# Independent list sets and per-row rooms (sb_alrev token rooms, computed without the builder's code).
visits = {r['video_id']: r['visit_id'] for r in csv.DictReader(open(LISTS/'authority_visits.raw'))}
norm = lambda x: ('scannetpp/'+x.split('/', 1)[1]) if x.startswith('scannetppv2/') else x
L = {'R0': {norm(x) for x in open(LISTS/'bdb5d402.raw').read().split()},
     'withheld-80': {norm(x) for x in json.load(open(LISTS/'634820b4.raw'))['rooms']},
     'BENCH v2': {norm(x) for x in json.load(open(LISTS/'3119aa4a.raw'))['physical_groups']},
     'dev-S1': {norm(x) for x in json.load(open(LISTS/'969cdb56.raw'))['physical_groups']},
     'K1': {c['room'] for c in json.load(open(LISTS/'4d4736cf.raw'))['captures'] if c['k1_split'] == 'heldout'}}
row = Counter()
recount = Counter()
mine_rows = {}
with ro(HERE/'v7_rerun/rows.sqlite') as c:
    for idx, token, scene, room, tier, hits, reason in c.execute('SELECT row_index,token,scene,room,tier,hits,unresolved_reason FROM rows'):
        mine_rows[idx] = (token, scene, room, tier, hits, reason)
        row['rows'] += 1
        row['scene_and_room_nonnull'] += bool(scene and room)
        t = tok.get(token)
        if t is None:
            row['token_missing_in_sb_alrev'] += 1
        else:
            row['scene_eq'] += t['canonical'] == scene
            row['room_eq'] += t['room'] == room
            row['tier_eq'] += t['tier'] == tier
        got = sorted(json.loads(hits))
        want = sorted(n for n in NAMES if room in L[n])
        row['hits_eq_independent'] += got == want
        for n in want:
            recount[n] += 1
out['per_row_vs_sb_alrev'] = dict(row)
out['independent_recount'] = {n: recount[n] for n in NAMES}
eq = 0
with ro(O/'sb_auditfix/out/v7/rows.sqlite') as c:
    for r in c.execute('SELECT row_index,token,scene,room,tier,hits,unresolved_reason FROM rows'):
        eq += mine_rows.get(r[0]) == tuple(r[1:])
out['vs_builder_rows'] = dict(rows_equal=eq, rerun_rows_sha=sha(HERE/'v7_rerun/rows.sqlite'),
                              builder_rows_sha=sha(O/'sb_auditfix/out/v7/rows.sqlite'))

# Raw-store exposure to the probe gaps: multiple canonical witnesses and loose native syntax.
fields = Counter()
multi = Counter()
loose = Counter()
with ro(STORE) as c:
    for i, raw in c.execute('SELECT i,row FROM rows'):
        r = json.loads(raw)
        vals = []
        for name, v in (('row', r), ('provenance', r.get('provenance') or {}), ('ground_record', r.get('ground_record') or {}),
                        ('gt_authority', r.get('gt_authority') or {})):
            if isinstance(v, dict) and v.get('canonical'):
                fields[name] += 1
                vals.append(v['canonical'])
        if len(vals) > 1:
            multi['rows_with_2plus_witnesses'] += 1
            multi['rows_with_disagreeing_witnesses'] += len(set(vals)) > 1
        scene = mine_rows[i][1]
        ds, cap = scene.split('/', 1)
        if ds == 'scannet' and not re.fullmatch(r'scene\d{4}_\d{2}', cap):
            loose['scannet_not_4_2_digits'] += 1
        if ds == 'arkitscenes':
            loose['arkit_rows'] += 1
            loose['arkit_not_in_visits'] += cap not in visits
            loose['arkit_leading_zero'] += cap.startswith('0')
            loose['arkit_capture_room'] += mine_rows[i][2].startswith('arkitscenes/capture')
out['store_witness_fields'] = dict(fields)
out['store_multi_witness'] = dict(multi)
out['store_loose_syntax'] = dict(loose)
(HERE/'v7_compare_out.json').write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
print(json.dumps({k: v for k, v in out.items() if k != 'inputs'}, indent=1, sort_keys=True))
