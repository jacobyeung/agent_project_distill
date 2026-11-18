"""Build ROOM_CROSSWALK.json: every item of the pooled harm rule's two sets -> one canonical physical room.

Canonical physical room keys (one namespace for both sets, so disjointness is a set test):
  ScanNet     scannet/sceneNNNN          (all rescans sceneNNNN_XX of one room; the R0 census key)
  ScanNet++   scannetpp/<scene id>       (v1 and v2 share scene ids; ScanNet++ defines no grouping across scenes)
  ARKitScenes arkitscenes/venue<visit_id> from 3dod/metadata.csv (visit NA -> arkitscenes/video<video_id>)
dev-S1 (family main): the item's native scene (A544.jsonl `scene`) gives the canonical room; the read's room label
  (`d1/...`, `d2/...`, `d3/...`) must name exactly one canonical room and each canonical room exactly one label.
R0-dev (family a7): the read carries opaque room and scene labels; the lane cont_ops identifier map
  (h1read/evidence/ID_MAP.json, the same map h1pair.py decodes with) gives each logical item id its native room
  `scannetpp/<id>`; the opaque label must name exactly one native room and each native room exactly one label;
  every native room must be on the R0-dev list (R0_DEV_ROOMS.txt) and on the registered R0 room list bdb5d402.
Room order inside a set: the sorted order of the read's room labels (the order the registered intervals were drawn in).
usage: build_crosswalk.py OUT.json"""
import collections, csv, hashlib, json, re, sys

C = '/scratch/jjyeung/orch_n30/cont_ops/work'
EV = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/b10_reserve/'
SRC = dict(
    dev_s1_baseline=C + '/d0/readk/evidence/A544.jsonl',
    r0_dev_baseline=C + '/h1read/kit/build/adff67f7ae9/fetched/x/ITEMS.jsonl',
    id_map=C + '/h1read/evidence/ID_MAP.json',
    arkit_metadata='/scratch/jjyeung/orch_n30/pooled_rule2/work/arkit_3dod_metadata.csv',
    r0_rooms=EV + 'R0_ROOMS.txt',
    r0_dev_rooms=EV + 'R0_DEV_ROOMS.txt')
PIN = dict(dev_s1_baseline='8347cd843f47fe637e770e47544ad49b03e60909e5312260a305319150edb8be',
           r0_dev_baseline='a05c2318e038d6e19c368c309d8cba2cd31047fc6fd7ef124a7b8ac943565233',
           r0_rooms='bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3')
S_TYPES = ('object_counting', 'object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard',
           'object_rel_distance', 'object_size_estimation', 'route_planning')
R_TYPES = S_TYPES[:6] + ('obj_appearance_order',)


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def rows(p, fam, types):
    return [r for r in (json.loads(l) for l in open(p) if l.strip()) if r['family'] == fam and r['task_type'] in types]


def arkit_venues(path):
    out = {}
    for r in csv.DictReader(open(path)):
        v = r['visit_id'].strip()
        out[r['video_id'].strip()] = 'arkitscenes/venue' + v if v and v != 'NA' else 'arkitscenes/video' + r['video_id'].strip()
    return out


def dev_s1_room(scene, venues):
    ds, sid = scene.split('/', 1)
    if ds == 'scannet':
        m = re.fullmatch(r'(scene\d{4})_\d{2}', sid)
        if not m:
            raise SystemExit('unparsable ScanNet scene ' + scene)
        return 'scannet/' + m.group(1)
    if ds in ('scannetpp', 'scannetppv2'):
        if not re.fullmatch(r'[0-9a-f]+', sid):
            raise SystemExit('unparsable ScanNet++ scene ' + scene)
        return 'scannetpp/' + sid
    if ds == 'arkitscenes':
        if sid not in venues:
            raise SystemExit('ARKitScenes video absent from metadata.csv: ' + scene)
        return venues[sid]
    raise SystemExit('unknown dataset ' + scene)


def bijection(name, pairs):
    """pairs: (label, canonical room) per item -> label->room map; refuses a label on two rooms or a room on two labels."""
    l2r, r2l = {}, {}
    for lab, room in pairs:
        if l2r.setdefault(lab, room) != room:
            raise SystemExit('%s: label %s names two physical rooms (%s, %s)' % (name, lab, l2r[lab], room))
        if r2l.setdefault(room, lab) != lab:
            raise SystemExit('%s: physical room %s carries two labels (%s, %s)' % (name, room, r2l[room], lab))
    return l2r


def build():
    for k, v in PIN.items():
        if sha(SRC[k]) != v:
            raise SystemExit('%s is not the pinned file' % k)
    venues = arkit_venues(SRC['arkit_metadata'])
    r0 = set(l.strip() for l in open(SRC['r0_rooms']) if l.strip())
    r0dev = set(l.strip() for l in open(SRC['r0_dev_rooms']) if l.strip())
    out = dict(schema='pooled-rule-room-crosswalk-v1', sources={k: dict(path=v, sha256=sha(v)) for k, v in SRC.items()},
               keys='scannet/sceneNNNN | scannetpp/<scene id> | arkitscenes/venue<visit_id> (visit NA: arkitscenes/video<id>)',
               room_order='sorted order of the read room labels inside each set', sets={})
    # dev-S1
    S = rows(SRC['dev_s1_baseline'], 'main', S_TYPES)
    items, pairs, scenes = {}, [], {}
    for r in S:
        room = dev_s1_room(r['scene'], venues)
        if r['id'] in items:
            raise SystemExit('duplicate dev-S1 item ' + r['id'])
        items[r['id']] = room
        pairs.append((r['room'], room))
        if scenes.setdefault(r['scene'], room) != room:
            raise SystemExit('dev-S1 scene on two rooms ' + r['scene'])
    l2r = bijection('dev-S1', pairs)
    out['sets']['dev-S1'] = dict(family='main', items=items, label_to_room=l2r, scene_to_room=scenes,
                                 room_order=[l2r[l] for l in sorted(l2r)])
    # R0-dev
    idmap = json.load(open(SRC['id_map']))
    logical = {}
    for opaque, v in idmap.items():
        if v['id'] in logical:
            raise SystemExit('identifier map holds logical id twice: ' + v['id'])
        if v.get('dataset') != 'scannetpp' or not re.fullmatch(r'scannetpp/[0-9a-f]+', v['room']) or v['room'] != 'scannetpp/' + v['scene']:
            raise SystemExit('identifier map entry is not a ScanNet++ room: %s' % opaque)
        logical[v['id']] = v['room']
    R = rows(SRC['r0_dev_baseline'], 'a7', R_TYPES)
    items, pairs, scenes = {}, [], {}
    for r in R:
        if r['id'] not in logical:
            raise SystemExit('R0-dev item absent from the identifier map: ' + r['id'])
        if r['id'] in items:
            raise SystemExit('duplicate R0-dev item ' + r['id'])
        room = logical[r['id']]
        if room not in r0dev or room not in r0:
            raise SystemExit('R0-dev item on a room outside the R0-dev list: %s %s' % (r['id'], room))
        items[r['id']] = room
        pairs.append((r['room'], room))
        if scenes.setdefault(r['scene'], room) != room:
            raise SystemExit('R0-dev scene label on two rooms ' + r['scene'])
    l2r = bijection('R0-dev', pairs)
    out['sets']['R0-dev'] = dict(family='a7', items=items, label_to_room=l2r, scene_to_room=scenes,
                                 room_order=[l2r[l] for l in sorted(l2r)])
    a, b = set(out['sets']['dev-S1']['room_order']), set(out['sets']['R0-dev']['room_order'])
    if a & b:
        raise SystemExit('physical rooms in both sets: %s' % sorted(a & b))
    if a & r0:
        raise SystemExit('dev-S1 rooms on the R0 list: %s' % sorted(a & r0))
    out['summary'] = {k: dict(items=len(v['items']), rooms=len(v['room_order']),
                              rooms_by_dataset=dict(collections.Counter(x.split('/')[0] for x in v['room_order'])),
                              multi_scene_rooms=sum(1 for x in v['room_order'] if sum(1 for s, y in v['scene_to_room'].items() if y == x) > 1))
                      for k, v in out['sets'].items()}
    out['summary']['R0-dev']['r0_dev_rooms_without_items'] = sorted(r0dev - b)
    out['summary']['shared_rooms'] = 0
    return out


if __name__ == '__main__':
    x = build()
    s = json.dumps(x, indent=1, sort_keys=True) + '\n'
    open(sys.argv[1], 'w').write(s)
    print(json.dumps(x['summary']))
    print('sha256', hashlib.sha256(s.encode()).hexdigest())
