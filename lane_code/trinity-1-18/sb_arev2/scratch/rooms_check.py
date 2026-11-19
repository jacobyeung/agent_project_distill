"""Independent room-rule check of the training rows and of the whole recovered extract (system python, no N imports)."""
import csv, gzip, hashlib, io, json, re
from collections import Counter, defaultdict
from pathlib import Path

B = Path('/scratch/jjyeung/orch_n30')
OUT = B/'sb_rowA/out'
SRC = B/'sb_evidence/aws_sources/ap__8865619b__runs__469ddece__inputs__prepare_dd26bb95f37a43789206c6e4d4cd94bd__routing__rows.camera_rows.jsonl.gz'
I18 = B/'tree_rebuild10_w/w18/work/build18/inputs'
PINS = dict(split=(I18/'27126674a57111585615308cb3e779e169b5693b1c87afafe691ce8e56c2b390.json', '27126674'),
            reserve=(I18/'bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3.json', 'bdb5d402'),
            visits=(I18/'657020f2d1119220b5068176ffc7298a8585076468407b60d8f5e3e6223442ca.json', '657020f2'),
            teacher=(B/'sb_alias2/work/TEACHER_K1.raw', '4d4736cf'),
            withheld=(B/'tree_rebuild10_w/w16/fixtures/work/shared/WITHHELD_ROOMS_80.json', '634820b4'),
            devs1=(B/'tree_rebuild10_w/w16/fixtures/work/kit07ca49df_meta/m/k/dev_scene_exclusions.json', '969cdb56'),
            bench=(B/'tree_rebuild10_w/w16/fixtures/work/kit07ca49df_meta/m/k/benchmark_scene_exclusions.json', '3119aa4a'),
            merged=(B/'tree_rebuild10_w/w17b/work/tree_r1/student_pilot/r2_dev_merged.json', 'a1869ae2'),
            alias=(B/'sb_alias2/out/TIERED_ALIAS_MAP.json', None))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
H = {k: sha(p) for k, (p, _) in PINS.items()}
for k, (p, pre) in PINS.items(): assert pre is None or H[k].startswith(pre), (k, H[k])
J = {k: json.loads(Path(p).read_text()) for k, (p, _) in PINS.items() if k not in ('reserve', 'visits')}
visits = {r['video_id']: r['visit_id'] for r in csv.DictReader(io.StringIO(PINS['visits'][0].read_text()))}
NATIVE = dict(scannet='scannet', scannetpp='scannetppv2', scannetppv2='scannetppv2', arkitscenes='arkitscenes')
TOK = dict(scannet='d1', scannetpp='d2', scannetppv2='d2', arkitscenes='d3')
DS = dict(d1='scannet', d2='scannetpp', d3='arkitscenes', scannet='scannet', scannetpp='scannetpp', scannetppv2='scannetpp', arkitscenes='arkitscenes')


def mint(canonical):
    ds, sc = canonical.split('/', 1)
    return TOK[ds] + '/v' + hashlib.sha256(f'rung1 scene {NATIVE[ds]}/{sc}'.encode()).hexdigest()[:12]


def room(name):
    """Physical room of a real (non-token) scene name; None for opaque tokens."""
    ds, sc = name.split('/', 1); ds = DS.get(ds, ds)
    if re.fullmatch(r'v[0-9a-f]{12}', sc): return None
    if ds == 'scannet':
        m = re.match(r'(scene\d{4})', sc); return 'scannet/' + m[1] if m else None
    if ds == 'scannetpp': return 'scannetpp/' + sc
    if ds == 'arkitscenes':
        if sc.startswith('venue') or sc.startswith('capture'): return 'arkitscenes/' + sc
        v = visits.get(sc); return 'arkitscenes/venue' + v if v and v != 'NA' else 'arkitscenes/capture' + sc
    return ds + '/' + sc


def tok(name):
    ds, sc = name.split('/', 1)
    return (TOK.get(ds, ds) if ds in TOK else ds) + '/' + sc if re.fullmatch(r'v[0-9a-f]{12}', sc) else None


def names_to_sets(names):
    rooms, toks = set(), set()
    for n in names:
        if not isinstance(n, str) or '/' not in n: continue
        t = tok(n)
        if t: toks.add(t)
        else:
            r = room(n)
            if r: rooms.add(r)
            try: toks.add(mint(n if not n.startswith(('d1/', 'd2/', 'd3/')) else DS[n[:2]] + n[2:]))
            except Exception: pass
    return rooms, toks


S = {}
split = J['split']
assert split['teacher_k1']['sha256'] == H['teacher']
S['K1'] = names_to_sets([c['room'] for c in split['teacher_k1']['captures'] if c['k1_split'] == 'heldout']
                        + [c['canonical'] for c in split['teacher_k1']['captures'] if c['k1_split'] == 'heldout'])
S['R0'] = names_to_sets([l.strip() for l in PINS['reserve'][0].read_text().splitlines() if l.strip()]
                        + [c['room'] for c in split['r0_scenes']['captures'].values()])
w = J['withheld']; S['withheld-80'] = names_to_sets(w['rooms'] + [a for k, v in w['aliases'].items() for a in [k, *v]])
for key, name in (('devs1', 'dev-S1'), ('merged', 'merged-dev')):
    d = J[key]; S[name] = names_to_sets(d['physical_groups'] + d['rooms'] + d['natives'] + [a for k, v in d['aliases'].items() for a in [k, *v]]
                                        + [a for v in d['canonical'].values() for a in v])
b = J['bench']; S['BENCH v2'] = names_to_sets(b['physical_groups'] + b['scenes'] + ['/'.join(x) for x in b['rung1_tokens']]
                                             + [m['group'] for m in b['members'].values()])
for name, path in (('heldout-items', OUT/'HELDOUT_CAMERA_ITEMS.json'), ('devs1-items', B/'sb_callrate/in/cont_ops/work/r1route/out3/bases/b1/src/items/devs1_routed.json'),
                   ('r0dev-items', B/'sb_callrate/in/cont_ops/work/r1route/out3/bases/b1/src/items/r0dev.json')):
    its = json.loads(path.read_text())['items']; H[name] = sha(path)
    S[name] = names_to_sets([x for it in its for x in (it.get('room_key'), it.get('scene'), it.get('room') if '/v' not in str(it.get('room')) else None) if x])
sizes = {k: (len(r), len(t)) for k, (r, t) in S.items()}
# removal lists (row keys) and K1 canonicals from N's config plus the K1 union
cfg = json.loads((B/'tree_rebuild10_w/w19/work/build19/inputs/config.json').read_text())
rm_keys = defaultdict(set); rm_canon = set()
for p in [x['path'] for x in cfg['remove_files']] + [str(B/'sb_k1list/out/u_union.json')]:
    H['rm:' + Path(p).name] = sha(p)
    for line in Path(p).read_text().splitlines():
        if not line.strip(): continue
        try: v = json.loads(line)
        except Exception: continue
        if isinstance(v, dict):
            for k in ('row_key', 'qid'):
                if v.get(k): rm_keys[v[k]].add(Path(p).name)
            if v.get('canonical'): rm_canon.add(room(v['canonical']) or v['canonical'])
alias = J['alias']['aliases']


def check(r):
    rt = r['routing']; token = r['dataset'] + '/' + r['scene']; can = rt.get('canonical'); hits = []
    if not can: return ['NO_CANONICAL'], None
    if mint(can) != token: hits.append('TOKEN_NOT_MINTED_FROM_CANONICAL')
    a = alias.get(token)
    if a and room(a['canonical']) != room(can): hits.append('ALIAS_MAP_DISAGREES')
    rm = room(can)
    if rt.get('physical_group') and room(rt['physical_group']) != rm: hits.append('PHYSICAL_GROUP_DISAGREES')
    for name, (rooms, toks) in S.items():
        if rm in rooms or token in toks: hits.append('room:' + name)
    return hits, rm


rows = [json.loads(l) for l in open(OUT/'CAMERA_ROWS.jsonl')]; lin = [json.loads(l) for l in open(OUT/'CAMERA_LINEAGE.jsonl')]
tr = Counter(); tr_rooms = set(); ex = []
for r, l in zip(rows, lin):
    hits, rm = check(r); tr_rooms.add(rm)
    for h in hits: tr[h] += 1
    for q in (r['qid'], l['source_qid']):
        if q in rm_keys: tr['removal_list_key:' + ','.join(sorted(rm_keys[q]))] += 1
    if rm in rm_canon: tr['removal_list_canonical_room'] += 1
    if hits and len(ex) < 10: ex.append((r['qid'], rm, hits))
    if l['room'] != rm or l['canonical'] != r['routing']['canonical']: tr['lineage_room_differs'] += 1
# whole extract
full = defaultdict(Counter)
with gzip.open(SRC, 'rt') as f:
    for line in f:
        x = json.loads(line); r = json.loads(x['row']); t = r['routing']['question_type']
        hits, rm = check(r)
        if r['qid'] in rm_keys: hits.append('removal_key')
        full[t]['total'] += 1; full[t]['kept_by_rooms_and_keys' if not hits else 'dropped'] += 1
        for h in set(hits): full[t][h] += 1
res = dict(list_sizes_rooms_tokens=sizes, training=dict(tr), training_rooms=len(tr_rooms), training_examples=ex,
           training_rooms_in_heldout=len(tr_rooms & S['heldout-items'][0]), extract={k: dict(v) for k, v in full.items()}, sha256=H)
json.dump(res, open('/scratch/jjyeung/orch_n30/sb_arev2/scratch/rooms_check.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'sha256'}, indent=1))
