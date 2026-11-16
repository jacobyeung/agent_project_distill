#!/usr/bin/env python3
"""Reserve-scene census R0: which captures are outside every training stream of the
student lineage (C1-a -> T0 -> CP1 -> LEG-S1 -> D0), outside every benchmark room/venue
and dev set, and have ground truth on Trinity.

Inputs are local copies under ../in (see INPUTS in the output). Writes out/CENSUS.json.
Room keys: ScanNet sceneNNNN; ScanNet++ scene id; ARKitScenes 3DOD visit_id venue
(visit NA keeps the video alone).
"""
import csv, gzip, hashlib, json, os, sys
from collections import Counter, defaultdict

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(L, 'in')
K = os.path.join(IN, 'kit07', 'pull', 'm', 'k')
M3 = os.path.join(IN, 'kit07', 'pull', 'm3')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def rung1(ns, scene):
    return 'v' + hashlib.sha256(f'rung1 scene {ns}/{scene}'.encode()).hexdigest()[:12]


def posetok(ns, scene):  # posedata ARKit token family
    return 'v' + hashlib.sha256(f'{ns}/{scene}'.encode()).hexdigest()[:12]


DS = {'scannet': 'd1', 'scannetpp': 'd2', 'arkitscenes': 'd3'}
NS_R1 = {'scannet': 'scannet', 'scannetpp': 'scannetppv2', 'arkitscenes': 'arkitscenes'}


def lines(p):
    return [x.strip() for x in open(p) if x.strip()]


def build_universe():
    U = {}  # capture key -> record
    for s in lines(os.path.join(IN, 'scannet_scans.txt')):
        U[f'scannet/{s}'] = dict(dataset='scannet', native=s, room=f'scannet/{s[:9]}', split='scans', gt='mesh+instances+pose')
    for s in lines(os.path.join(IN, 'scannet_scans_test.txt')):
        U[f'scannet/{s}'] = dict(dataset='scannet', native=s, room=f'scannet/{s[:9]}', split='scans_test', gt='pose+mesh (no instances)')
    for s in lines(os.path.join(IN, 'scannetpp_scenes.txt')):
        U[f'scannetpp/{s}'] = dict(dataset='scannetpp', native=s, room=f'scannetpp/{s}', split='data', gt='mesh+instances+pose')
    local = set(lines(os.path.join(IN, 'arkit_training_local.txt')))
    with open(os.path.join(IN, 'arkit_metadata.csv')) as f:
        for r in csv.DictReader(f):
            v = r['video_id']; visit = r['visit_id']
            room = f'arkitscenes/venue{visit}' if visit and visit != 'NA' else f'arkitscenes/video{v}'
            U[f'arkitscenes/{v}'] = dict(dataset='arkitscenes', native=v, room=room, split=r['fold'],
                                          gt=('boxes+mesh+pose (local)' if v in local else 'not on Trinity'),
                                          sky=r['sky_direction'], local=v in local)
    for k, r in U.items():
        d = DS[r['dataset']]
        toks = {f"{d}/{rung1(NS_R1[r['dataset']], r['native'])}", f"{d}/{r['native']}"}
        for fam in ('v590kgt scene', 'rung1 scene', 'rung2 scene'):
            for ns in {NS_R1[r['dataset']], r['dataset'], 'scannetpp', 'scannetppv2'} if r['dataset'] == 'scannetpp' else {NS_R1[r['dataset']]}:
                toks.add(f"{d}/v" + hashlib.sha256(f"{fam} {ns}/{r['native']}".encode()).hexdigest()[:12])
        if r['dataset'] == 'arkitscenes':
            toks.add(f"{d}/{posetok('arkitscenes', r['native'])}")
        if r['dataset'] == 'scannetpp':
            toks.add(f"{d}/{rung1('scannetpp', r['native'])}")
        r['aliases'] = sorted(toks)
    return U


def main():
    U = build_universe()
    alias2cap = {}
    for k, r in U.items():
        for a in r['aliases']:
            alias2cap.setdefault(a, set()).add(k)
    room_caps = defaultdict(set)
    for k, r in U.items():
        room_caps[r['room']].add(k)

    inputs = {}
    def reg(name, path):
        inputs[name] = {'path': path, 'sha256': sha(path)}

    # ---------- training authorities ----------
    train_sets = {}  # name -> set of capture keys (strict) ; unresolved counts
    unresolved = {}

    def resolve(names, label):
        caps, un = set(), []
        for n in names:
            c = alias2cap.get(n)
            if c:
                caps |= c
            else:
                un.append(n)
        unresolved[label] = un
        return caps

    p = os.path.join(M3, 'a3v2_division.json'); reg('division_A3_f41d15aa', p)
    dv = json.load(open(p))
    train_sets['division_A3_train'] = resolve(dv['train_scenes'], 'division_A3_train')
    readout = resolve(dv['heldout_scenes'], 'division_A3_heldout')

    p = os.path.join(M3, 'frame_map.jsonl.gz'); reg('kit07_frame_map', p)
    fm = set()
    with gzip.open(p, 'rt') as f:
        for l in f:
            o = json.loads(l); fm.add(f"{o['d']}/{o['s']}")
    train_sets['kit07_frame_map_scenes'] = resolve(sorted(fm), 'kit07_frame_map_scenes')

    p = os.path.join(K, 'frame_rates.json'); reg('kit07_frame_rates', p)
    fr = json.load(open(p))
    train_sets['kit07_frame_rates_scenes'] = resolve(sorted(set(fr['by_scene']) | set(fr['missing_arkit_scenes'])), 'kit07_frame_rates_scenes')

    extra = os.path.join(IN, 'stream_scenes')  # optional per-stream scene lists (one key per line)
    if os.path.isdir(extra):
        for fn in sorted(os.listdir(extra)):
            if fn.endswith('.txt'):
                pth = os.path.join(extra, fn); reg('stream_' + fn, pth)
                train_sets['stream_' + fn[:-4]] = resolve(lines(pth), 'stream_' + fn[:-4])

    # ---------- benchmark / dev authorities (room level) ----------
    bench_rooms, bench_caps = set(), set()
    p = os.path.join(K, 'benchmark_scene_exclusions.json'); reg('bench_v2_3119aa4a', p)
    b = json.load(open(p))
    bench_rooms |= set(b['physical_groups'])
    bench_caps |= resolve(b['scenes'], 'bench_v2_scenes')
    for t in b['rung1_tokens']:
        bench_caps |= alias2cap.get(f'{t[0]}/{t[1]}', set())
    for nm in ['99e6eed6', '932c0c4e', 'dafa4a9c', '600ef69d']:
        p = os.path.join(K, nm + '.json'); reg('exclusions_' + nm, p)
        names = json.load(open(p))['names']
        # room-only names like d1/scene0011 expand to the room
        caps = set()
        un = []
        for n in names:
            if n in alias2cap:
                caps |= alias2cap[n]
            elif n.startswith('d1/scene') and len(n) == 12:
                caps |= room_caps.get('scannet/' + n[3:], set())
            elif n.startswith('d3/venue') or n.startswith('d3/video'):
                caps |= room_caps.get('arkitscenes/' + n[3:], set()); bench_rooms.add('arkitscenes/' + n[3:])
            else:
                un.append(n)
        unresolved['exclusions_' + nm] = un
        bench_caps |= caps
    dev_caps = set()
    p = os.path.join(K, 'dev_scene_exclusions.json'); reg('devS1_969cdb56', p)
    d = json.load(open(p))
    dev_rooms = set(d['physical_groups'])
    for n, al in d['aliases'].items():
        for a in al + [n]:
            dev_caps |= alias2cap.get(a, set())
    p = os.path.join(IN, 'WITHHELD_ROOMS_80.json'); reg('withheld80_634820b4', p)
    w = json.load(open(p))
    wrooms = set(w['rooms'])

    # ---------- expand to rooms ----------
    def rooms_of(caps):
        return {U[c]['room'] for c in caps}
    trained_caps = set().union(*train_sets.values())
    trained_rooms = rooms_of(trained_caps)
    bench_rooms_all = set(bench_rooms) | rooms_of(bench_caps)
    dev_rooms_all = dev_rooms | rooms_of(dev_caps) | wrooms
    readout_rooms = rooms_of(readout)

    per_cap = {}
    for k, r in U.items():
        room = r['room']
        reasons = []
        for nm, s in train_sets.items():
            if k in s: reasons.append('strict:' + nm)
        if room in trained_rooms and not any(x.startswith('strict') for x in reasons): reasons.append('room:trained')
        if room in bench_rooms_all: reasons.append('room:benchmark')
        if room in dev_rooms_all: reasons.append('room:dev_or_withheld')
        flags = []
        if room in readout_rooms: flags.append('a3_pose_readout_bank')
        per_cap[k] = dict(room=room, dataset=r['dataset'], split=r['split'], gt=r['gt'], reasons=reasons, flags=flags,
                          local=r.get('local', True))

    def summarize(pred):
        out = {}
        for ds in ['scannet', 'scannetpp', 'arkitscenes']:
            caps = [k for k, v in per_cap.items() if v['dataset'] == ds and pred(k, v)]
            out[ds] = {'captures': len(caps), 'rooms': len({per_cap[k]['room'] for k in caps})}
        return out

    clean = lambda k, v: not v['reasons']
    usable = lambda k, v: clean(k, v) and (v['dataset'] != 'arkitscenes' or v['local'])
    census = {
        'universe': summarize(lambda k, v: True),
        'clean_any_gt_location': summarize(clean),
        'clean_with_gt_on_trinity': summarize(usable),
        'clean_with_gt_on_trinity_vqa_capable': summarize(lambda k, v: usable(k, v) and v['split'] != 'scans_test'),
        'clean_on_trinity_excluding_readout_bank': summarize(lambda k, v: usable(k, v) and not v['flags']),
        'trained_by_authority': {nm: len(s) for nm, s in train_sets.items()},
        'unresolved_counts': {k: len(v) for k, v in unresolved.items()},
        'unresolved_examples': {k: v[:5] for k, v in unresolved.items() if v},
        'readout_bank_caps': len(readout),
        'inputs': inputs,
    }
    # room-level blockers per dataset for the narrative
    blk = Counter()
    for k, v in per_cap.items():
        key = (v['dataset'], v['split'], tuple(sorted({x.split(':')[0] + ':' + x.split(':')[1].split('_')[0] for x in v['reasons']})))
        blk[key] += 1
    census['reason_table'] = [[a, b, list(c), n] for (a, b, c), n in sorted(blk.items())]
    os.makedirs(os.path.join(L, 'out'), exist_ok=True)
    json.dump(census, open(os.path.join(L, 'out', 'CENSUS.json'), 'w'), indent=1)
    json.dump(per_cap, open(os.path.join(L, 'out', 'CENSUS_PER_CAPTURE.json'), 'w'))
    print(json.dumps({k: census[k] for k in ['universe', 'clean_any_gt_location', 'clean_with_gt_on_trinity', 'clean_with_gt_on_trinity_vqa_capable', 'clean_on_trinity_excluding_readout_bank', 'trained_by_authority', 'unresolved_counts', 'readout_bank_caps']}, indent=1))
    for row in census['reason_table']:
        print(row)


if __name__ == '__main__':
    main()
