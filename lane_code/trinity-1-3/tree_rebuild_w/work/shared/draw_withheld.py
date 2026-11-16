"""Draw the 80 withheld rooms (lane rows_rebuild, 2026-11-15).

Eligible rooms: the rooms (physical_group) of the sealed leg's room programs, i.e. the rows of the pool
room sets T0_room, T1H1_room, SCENE_room (SCENE_room_sppK was deferred and never trained) that survive
the kit's own filters: pool exclusion lists (dev-S1, eval rooms, room release gate; set+qid) and the
routing division a3v2 (train scenes, alias by the BENCH v2 token rule). The room unit rows were derived
from these same room programs, so they add no room. Then every room listed by any exclusion record is
removed: BENCH v2 (physical_groups, member groups), dev_scene_exclusions (rooms), own_probe EVAL_ROOMS
(evaluation/qualification rooms and the rooms of its scene lists), ofs_e1 ROOM_SPLIT (every scene list
and overlapping_rooms). ScanNet and ScanNet++ only. Draw: sorted list per dataset,
random.Random(20261115).sample(..., 40) for ScanNet first, then the same generator for ScanNet++.
"""
import gzip, hashlib, json, random, re, sys
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/rows_rebuild/work')
POOL = W/'pull/pool'; K = W/'s0/pull/m/k'
SETS = {'T0_room': '947c8d100170a348.jsonl.gz', 'T1H1_room': '137de4ba701eff93.jsonl.gz', 'SCENE_room': '43f9b9afc69c7dff.jsonl.gz'}
NATIVE = {'scannet': ('d1', 'scannet'), 'scannetpp': ('d2', 'scannetppv2'), 'scannetppv2': ('d2', 'scannetppv2')}

def token(native_dataset, scene):
    return 'v' + hashlib.sha256(('rung1 scene ' + native_dataset + '/' + scene).encode()).hexdigest()[:12]

def room_of(name):
    """Normalize a scene/room string to 'scannet/sceneNNNN' or 'scannetpp/<id>' (None for others)."""
    name = name.strip()
    m = re.match(r'^(?:d1/|scannet/)?(scene\d{4})(?:_\d{2})?$', name)
    if m: return 'scannet/' + m.group(1)
    m = re.match(r'^(?:d2/|scannetpp/|scannetppv2/)([0-9a-f]{10})$', name)
    if m: return 'scannetpp/' + m.group(1)
    return None

def main():
    pool_excl = set()
    for f in ('pool_exclusion_0.tsv', 'pool_exclusion_1.tsv', 'pool_exclusion_2.tsv'):
        for line in (K/f).read_text().splitlines():
            if line.strip(): pool_excl.add(tuple(line.split('\t')[:2]))
    division = set(json.load(open(W/'s0/pull/m3/a3v2_division.json'))['train_scenes'])
    eligible, stats = {}, {'rows': 0, 'pool_excluded': 0, 'outside_division': 0}
    for name, f in SETS.items():
        for line in gzip.open(POOL/f, 'rt'):
            r = json.loads(line); stats['rows'] += 1
            if (name, r['qid']) in pool_excl: stats['pool_excluded'] += 1; continue
            ds, scene = r['scene'].split('/', 1)
            d, native = NATIVE[ds]
            if d + '/' + token(native, scene) not in division: stats['outside_division'] += 1; continue
            room = room_of(r['physical_group']) or room_of(r['scene'])
            eligible.setdefault(room, []).append(r['qid'])
    excluded = set()
    b = json.load(open(K/'benchmark_scene_exclusions.json'))
    for g in b['physical_groups']: excluded.add(room_of(g) or g)
    for key, m in b['members'].items():
        excluded.add(room_of(m.get('group') or '') or room_of(key) or key)
    for s in b['scenes']: excluded.add(room_of(s) or s)
    dev = json.load(open(K/'dev_scene_exclusions.json'))
    for x in dev['rooms'] + dev['physical_groups'] + dev['natives']: excluded.add(room_of(x) or x)
    e = json.load(open(W/'excl/own_probe/out/EVAL_ROOMS.json'))
    for k in ('evaluation_rooms', 'qualification_rooms', 'tuning_scenes', 'clean_scenes', 'frames32_scenes'):
        for x in e[k]: excluded.add(room_of(x) or x)
    s = json.load(open(W/'excl/ofs_e1/out/ROOM_SPLIT.json'))
    for k in ('tuning_scenes', 'legacy_read_scenes', 'room_disjoint_scenes', 'overlapping_read_scenes', 'overlapping_rooms'):
        for x in s[k]: excluded.add(room_of(x) or x)
    pools = {'scannet': sorted(r for r in eligible if r and r.startswith('scannet/') and r not in excluded),
             'scannetpp': sorted(r for r in eligible if r and r.startswith('scannetpp/') and r not in excluded)}
    rng = random.Random(20261115)
    picked = rng.sample(pools['scannet'], 40) + rng.sample(pools['scannetpp'], 40)
    rooms = sorted(picked)
    canon = json.dumps(rooms, separators=(',', ':')).encode()
    aliases = {}
    for room in rooms:
        ds, name = room.split('/', 1)
        if ds == 'scannet':
            aliases[room] = sorted(['d1/' + token('scannet', f'{name}_{k:02d}') for k in range(7)] + [f'd1/{name}_{k:02d}' for k in range(7)])
        else:
            aliases[room] = sorted(['d2/' + token('scannetppv2', name), 'd2/' + name])
    out = dict(schema='withheld-rooms-v1', seed=20261115, rule=__doc__.strip(), rooms=rooms, aliases=aliases,
               alias_rule='ScanNet: every possible rescan _00.._06 as native name and BENCH v2 token; ScanNet++: native id and token (native_dataset scannetppv2)',
               eligible_counts={k: len(v) for k, v in pools.items()},
               eligible_rooms_total=len([r for r in eligible if r]), excluded_eligible=len([r for r in eligible if r in excluded]),
               source_rows=stats, rooms_sha256=hashlib.sha256(canon).hexdigest(),
               lost_list_sha256='bf737b729a8f9414f400a639d33e997242f1788353ccab5e0c4e1f0fdb12e09f')
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps({k: out[k] for k in ('eligible_counts', 'eligible_rooms_total', 'excluded_eligible', 'source_rows', 'rooms_sha256')}))

if __name__ == '__main__':
    main()
