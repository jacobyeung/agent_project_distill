#!/usr/bin/env python3
"""Freeze the reserve-scene list R0 from the census (out/CENSUS.json, out/CENSUS_PER_CAPTURE.json).

Pools by ground truth level:
  full    - rgb + instances + mesh + pose (ScanNet++ iphone+scans; ScanNet scans/ with aggregation)
  mesh    - ScanNet++ rgb + mesh + pose, no instance annotation; ScanNet scans_test (pose + mesh)
  pose    - ScanNet++ iphone rgb + pose only
R0-dev: the first DEV_ROOMS full-GT ScanNet++ rooms ordered by sha256('R0 split v1 ' + room) (one GT source for dev;
ScanNet .sens decoding is only needed for R0-rl). Everything else is R0-rl.
"""
import hashlib, json, os, sys

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEV_ROOMS = 100
SPLIT_SALT = 'R0 split v1 '
SPP_GT = ['iphone/rgb.mkv', 'iphone/pose_intrinsic_imu.json', 'iphone/colmap', 'scans/segments_anno.json',
          'scans/mesh_aligned_0.05.ply', 'scans/segments.json']


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def level(k, v, assets):
    if v['dataset'] == 'scannet':
        return 'full' if v['split'] == 'scans' else 'mesh'
    if v['dataset'] == 'scannetpp':
        a = assets[k.split('/', 1)[1]]
        have = {f for f, s in a.items() if s is not None}
        if set(SPP_GT) <= have:
            return 'full'
        if {'iphone/rgb.mkv', 'iphone/pose_intrinsic_imu.json', 'scans/mesh_aligned_0.05.ply'} <= have:
            return 'mesh'
        if {'iphone/rgb.mkv', 'iphone/pose_intrinsic_imu.json'} <= have:
            return 'pose'
        return None
    return None  # ARKitScenes: no clean capture has GT on Trinity


def main():
    out = os.path.join(L, 'out')
    census = json.load(open(os.path.join(out, 'CENSUS.json')))
    per = json.load(open(os.path.join(out, 'CENSUS_PER_CAPTURE.json')))
    assets = json.load(open(os.path.join(out, 'scannetpp_assets.json')))
    caps = {}
    for k, v in sorted(per.items()):
        if v['reasons'] or (v['dataset'] == 'arkitscenes' and not v['local']):
            continue
        lv = level(k, v, assets)
        if lv is None:
            continue
        caps[k] = dict(room=v['room'], dataset=v['dataset'], native_split=v['split'], gt_level=lv, census_flags=v['flags'])
    rooms = {}
    for k, c in caps.items():
        r = rooms.setdefault(c['room'], dict(captures=[], levels=set()))
        r['captures'].append(k); r['levels'].add(c['gt_level'])
    # a room is full only if every capture is full (ScanNet rescans share one room)
    full_rooms = sorted((r for r, d in rooms.items() if d['levels'] == {'full'} and r.startswith('scannetpp/')),
                        key=lambda r: hashlib.sha256((SPLIT_SALT + r).encode()).hexdigest())
    dev = set(full_rooms[:DEV_ROOMS])
    for k, c in caps.items():
        c['r0_split'] = 'R0-dev' if c['room'] in dev else 'R0-rl'
        c['room_hash'] = hashlib.sha256((SPLIT_SALT + c['room']).encode()).hexdigest()
        c['proof'] = {'absent_from': sorted(census['inputs']), 'checks': 'capture aliases (native, rung1/rung2/v590kgt/posedata token families) and physical room absent from every listed authority; census reasons == []'}
    authorities = {n: d['sha256'] for n, d in census['inputs'].items()}
    counts = {}
    for c in caps.values():
        key = f"{c['r0_split']}|{c['dataset']}|{c['gt_level']}"
        counts[key] = counts.get(key, 0) + 1
    room_counts = {s: len({c['room'] for c in caps.values() if c['r0_split'] == s}) for s in ('R0-dev', 'R0-rl')}
    doc = dict(schema='reserve-scenes-r0-v1', rule=__doc__.strip(), dev_rooms=DEV_ROOMS, split_salt=SPLIT_SALT,
               authorities=authorities, census_sha256=sha(os.path.join(out, 'CENSUS.json')),
               per_capture_sha256=sha(os.path.join(out, 'CENSUS_PER_CAPTURE.json')),
               assets_sha256=sha(os.path.join(out, 'scannetpp_assets.json')),
               capture_counts=counts, room_counts=room_counts,
               rooms=sorted(rooms), dev_room_list=sorted(dev), captures=caps,
               exclusion_rule_for_later_legs='Exclude every room in `rooms` (all captures of the room, every stream: pose, VQA, routing, pointing, rasters, RL).')
    p = os.path.join(out, 'R0_SCENES.json')
    json.dump(doc, open(p, 'w'), indent=1, sort_keys=True)
    print(p, sha(p)); print(json.dumps(counts, indent=1)); print(room_counts)


if __name__ == '__main__':
    main()
