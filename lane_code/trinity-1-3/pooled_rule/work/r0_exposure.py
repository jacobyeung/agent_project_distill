"""R0 exposure audit of a row store: does any row sit on a reserve (R0) room?
Reads every row of rows.sqlite (read-only), resolves its scene alias to a canonical capture through the rows lane's alias maps
or the row's own provenance, and tests the canonical capture against the native id of each R0 room
(ScanNet++ 10-hex scene id, ScanNet sceneNNNN).  Rows that resolve through neither are counted and listed, not passed.
usage: r0_exposure.py ROWS.sqlite OUT.json"""
import sys, json, re, sqlite3, hashlib, collections
EV = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/b10_reserve/'
MAPS = ('/scratch/jjyeung/orch_n30/rows_a2/work/alias_map.json', '/scratch/jjyeung/orch_n30/b12_cntapp/work/d3_token_map.json')
r0 = [l.strip() for l in open(EV + 'R0_ROOMS.txt') if l.strip()]
dev = set(l.strip() for l in open(EV + 'R0_DEV_ROOMS.txt') if l.strip())
native = {r.split('/', 1)[1]: r for r in r0}
HEX = re.compile(r'(?<![0-9a-f])[0-9a-f]{10}(?![0-9a-f])')
SCN = re.compile(r'scene\d{4}')
amap = {}
for p in MAPS:
    amap.update(json.load(open(p)))
# third resolver: the counting/appearance lane's eligibility table (alias -> canonical capture)
ELIG = '/scratch/jjyeung/orch_n30/b12_cntapp/work/ELIGIBILITY_SCENES.json'
elig = {k: v['canonical'] for k, v in json.load(open(ELIG)).items() if v.get('canonical')}
conflict = sorted(k for k in elig if k in amap and amap[k] != elig[k])
for k, v in elig.items():
    amap.setdefault(k, v)
MAPS = MAPS + (ELIG,)


def r0_room(canonical):
    for tok in set(HEX.findall(canonical)) | set(SCN.findall(canonical)):
        if tok in native:
            return native[tok]
    return None


con = sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True)
n = 0
hits = collections.Counter()
hit_rows = []
by_ds = collections.Counter()
how = collections.Counter()
unresolved = collections.Counter()
unresolved_examples = {}
canon = collections.Counter()
unres_prov = collections.Counter()
unres_sample = {}
for i, raw in con.execute('select i,row from rows'):
    r = json.loads(raw)
    n += 1
    ds = str(r.get('dataset'))
    by_ds[ds] += 1
    alias = ds + '/' + str(r.get('scene'))
    can = amap.get(alias)
    if can:
        how['alias_map'] += 1
    else:
        can = (r.get('provenance') or {}).get('canonical')
        if can:
            how['provenance'] += 1
    if not can:
        unresolved[ds] += 1
        unresolved_examples.setdefault(alias, r.get('question_type'))
        pv = r.get('provenance') or {}
        unres_prov[(str(pv.get('frame_map_sha256')), str(r.get('pool')), str(pv.get('source', '')).rsplit('/', 1)[0],
                    str((r.get('retrace') or {}).get('rule')))] += 1
        if not unres_sample:
            unres_sample.update(dict(i=i, provenance=pv))
        continue
    canon[can] += 1
    room = r0_room(can)
    if room:
        hits['r0_dev' if room in dev else 'r0_rl'] += 1
        if len(hit_rows) < 20:
            hit_rows.append(dict(i=i, room=room, canonical=can, type=r.get('question_type')))
pos = sorted(c for c in canon if c.startswith('scannetppv2/'))[0]
out = dict(store=sys.argv[1], rows=n, rows_by_dataset=dict(by_ds), resolved_by=dict(how), distinct_canonical=len(canon),
           unresolved_rows=dict(unresolved), unresolved_aliases=len(unresolved_examples),
           unresolved_alias_list=dict(sorted(unresolved_examples.items())), map_conflicts=conflict,
           unresolved_by_provenance=[dict(frame_map_sha256=k[0], pool=k[1], source_dir=k[2], retrace_rule=k[3], rows=v)
                                     for k, v in sorted(unres_prov.items())],
           unresolved_sample=unres_sample,
           r0_rooms=len(r0), r0_dev_rooms=len(dev),
           r0_rooms_sha256=hashlib.sha256(open(EV + 'R0_ROOMS.txt', 'rb').read()).hexdigest(),
           r0_dev_rooms_sha256=hashlib.sha256(open(EV + 'R0_DEV_ROOMS.txt', 'rb').read()).hexdigest(),
           alias_maps={p: hashlib.sha256(open(p, 'rb').read()).hexdigest() for p in MAPS},
           hits=dict(hits), hit_rows=hit_rows,
           controls=dict(
               store_scene_is_not_r0=dict(canonical=pos, r0=r0_room(pos)),
               r0_dev_room_is_caught=dict(canonical='scannetppv2/' + sorted(dev)[0].split('/', 1)[1],
                                          r0=r0_room('scannetppv2/' + sorted(dev)[0].split('/', 1)[1])),
               r0_scannet_room_is_caught=dict(canonical='scannet/scene0183_00', r0=r0_room('scannet/scene0183_00'))))
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'hit_rows'}))
