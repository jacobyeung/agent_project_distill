"""Build pinned O1 manifests from local metadata; inspect admitted RGB headers only."""
import collections
import csv
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

from PIL import Image
from provenance import sha256, receipt, write_json

ROOT = Path(__file__).resolve().parents[1]
O = ROOT.parent
sys.path.insert(0, str(ROOT/'out'))
import room_gate as gate


def load(path):
    return json.loads(Path(path).read_text())


def main():
    out = ROOT/'out'
    paths = dict(bench=O/'revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json',
                 venue=O/'revsi_dev/v2work/arkit_3dod_metadata.csv',
                 splits=O/'verify_kit/out/SPLITS.json', rooms=O/'ofs_e1/out/ROOM_SPLIT.json',
                 memberships=O/'tlabel_intake/out/evaluation_memberships.json',
                 qualification=O/'tlabel_intake/out/TRAINING_EXCLUSIONS.json',
                 policy=O/'hrp_rows/out/scene_policy.json', sources=O/'hrp_rows/out/local_sources.json',
                 rgb=O/'hrp_rows/out/local_rgb_index.json', inventory=O/'hrp_rows/out/inventory.json',
                 candidates=O/'verify_kit/out/e1_k5_candidates.jsonl')
    cfg = dict(seed=17, validation_fraction=.2, rgb_headers_only=True,
               membership_rule='TRAINING_EXCLUSIONS binds opaque qualification example IDs to rooms')
    pins = receipt(paths.values(), [__file__, out/'room_gate.py', ROOT/'work/provenance.py', O/'hrp_rows/work/hrp.py'], cfg)
    bench, splits, quals, policy = (load(paths[k]) for k in ('bench', 'splits', 'qualification', 'policy'))
    if sha256(paths['bench']) != '3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970':
        raise ValueError('Benchmark authority pin differs')
    if sha256(paths['venue']) != bench['inputs'][str(paths['venue'])]:
        raise ValueError('Venue source pin differs')
    arkit = {}
    with paths['venue'].open() as f:
        for r in csv.DictReader(f):
            vid, venue = r['video_id'], r['visit_id']
            arkit[vid] = 'arkitscenes/' + (vid if venue in ('NA', '') else 'venue'+venue)
    for key, member in bench['members'].items():
        if key.startswith('d3/'):
            arkit[key.split('/')[1]] = member['group']
    arkit['43649472'] = 'arkitscenes/43649472'
    def physical(key):
        d, s = key.split('/')
        d = gate.dataset_name(d)
        if d == 'arkitscenes':
            if s.startswith('venue'):
                return d+'/'+s
            s = s.removeprefix('video')
            if s == '43649472':
                arkit.setdefault(s, d+'/'+s)  # Explicit metadata-absent singleton in exclusion record.
            return arkit[s]
        return d+'/'+(s[:-3] if d == 'scannet' and len(s) == 12 else s)
    excluded = {physical(k) for k in bench['physical_groups']}
    excluded.update(physical(k) for k in quals['room_ids'])
    # Preserve the HRP policy's stricter exclusions for the three supported corpora.
    excluded.update(physical(k) for k in policy['blocked_rooms'] if k.split('/')[0] in gate.ALIASES)
    excluded.update(physical(k) for k in splits['all_scenes'])
    frames_root = O/'ttower/work/frames32'
    frame_scenes = sorted(p.name.replace('__', '/') for p in frames_root.iterdir() if p.is_dir())
    excluded.update(physical(k) for k in frame_scenes)
    alias_rooms = {alias:physical(policy['room'][native]) for alias,native in policy['alias'].items()
                   if native in policy['room'] and native.split('/')[0] in gate.ALIASES}
    auth = dict(schema='own-room-gate-v1', evaluation_rooms=sorted(excluded), arkit_rooms=arkit, alias_rooms=alias_rooms,
                tuning_scenes=splits['tuning_scenes'], clean_scenes=splits['room_disjoint_scenes'],
                qualification_rooms=sorted(physical(k) for k in quals['room_ids']),
                frames32_scenes=frame_scenes, provenance=pins)
    write_json(out/'EVAL_ROOMS.json', auth)
    (out/'EVAL_ROOMS.sha256').write_text(sha256(out/'EVAL_ROOMS.json')+'  EVAL_ROOMS.json\n')
    authority_sha = sha256(out/'EVAL_ROOMS.json')
    gate.authority.cache_clear()
    assert all(gate.is_evaluation_room(*k.split('/')) for k in frame_scenes)
    entries, rgb = load(paths['sources']), load(paths['rgb'])
    dropped, admitted = [], []
    for e in entries:
        if e['source'] != 'b2_pool':
            continue
        native = policy['alias'][e['scene']]
        d, s = e['canonical'].split('/')
        d = gate.dataset_name(d)
        old_allowed = (e['scene'] in policy['train_scenes'] and e['scene'] not in policy['heldout_scenes']
                       and native not in policy['blocked_natives'] and policy['room'][native] not in policy['blocked_rooms'])
        reason = ('hrp_policy' if not old_allowed else
                  'qualification_or_benchmark_room' if gate.is_evaluation_room(d, s) else
                  'RGB_join_incomplete' if e['local_frame_count'] != 32 else None)
        if reason:
            dropped.append(dict(scene=e['canonical'], reason=reason, local_frames=e['local_frame_count']))
        else:
            gate.check_row(dict(dataset=d, scan=s, split='train'))
            admitted.append((e, d, s, gate.room(d, s)))
    rooms = sorted({r for _, _, _, r in admitted})
    random.Random(17).shuffle(rooms)
    val = set(rooms[:round(.2*len(rooms))])
    source_pins, counts, scenes = {}, collections.Counter(), collections.defaultdict(set)
    spec = importlib.util.spec_from_file_location('hrp_reader', O/'hrp_rows/work/hrp.py')
    hrp = importlib.util.module_from_spec(spec); spec.loader.exec_module(hrp)
    reader = hrp.Reader(rate=100_000_000)
    with (out/'b2_manifest.jsonl').open('w') as f:
        for e, d, s, r in admitted:
            gate.guard_path(e['mask']['path'], 'training')
            gate.guard_path(e['visibility']['path'], 'training')
            masks, labels, used, frames, indices = hrp.decode_source(e, reader)
            source_pins[e['mask']['path']] = e['mask']['sha256']
            source_pins[e['visibility']['path']] = e['visibility']['sha256']
            for slot, ref in enumerate(frames):
                pin = rgb[ref['sha256']]
                path = Path(pin['path'])
                gate.guard_path(path, 'training')
                if not str(path.resolve()).startswith('/scratch/'):
                    raise ValueError('Nonlocal RGB')
                with Image.open(path) as im:
                    wh = list(im.size)
                row = dict(dataset=d, scan=s, scene=f'{d}/{s}', room=r, slot=slot,
                           frame_index=int(indices[slot]), rgb_path=str(path), rgb_sha256=pin['sha256'],
                           raster_path=e['mask']['path'], raster_sha256=e['mask']['sha256'],
                           raster_encoding=e['encoding'], raster_hw=[240, 320], image_size=wh,
                           image_size_hw=list(reversed(wh)), split='val' if r in val else 'train',
                           instances=[dict(instance_id=i, name=name, pixel_area=int(masks[i][slot].sum()))
                                      for i, name in sorted(labels.items())],
                           source_scene=e['scene'], authority_sha256=authority_sha)
                gate.check_row(row)
                f.write(json.dumps(row, sort_keys=True)+'\n')
                counts[d+'/'+row['split']] += 1
                scenes[d+'/'+row['split']].add(s)
            print(f'manifest: {d}/{s}', flush=True)
    # Read candidate metadata to obtain names; never open an evaluation image or mask here.
    candidate_path = O/'verify_kit/out/e1_k5_candidates.jsonl'
    tuning = set(splits['tuning_scenes'])
    objects = collections.defaultdict(list)
    with candidate_path.open() as f:
        for line in f:
            row = json.loads(line)
            if row['scene'] in tuning:
                gate.check_row(row, 'tuning')
                objects[row['scene']].append(row)
    with (out/'tuning_manifest.jsonl').open('w') as f:
        for scene in sorted(tuning):
            d, s = scene.split('/')
            names = sorted(x['name'] for x in objects[scene])
            assert names
            for slot in range(32):
                row = dict(dataset=d, scan=s, scene=scene, room=gate.room(d, s), slot=slot,
                           frame_index=objects[scene][0]['frame_indices'][slot], names=names,
                           rgb_path=str(frames_root/scene.replace('/', '__')/f'{slot}.jpg'),
                           image_size=[640,480], image_size_hw=[480,640], split='tuning',
                           authority_sha256=authority_sha)
                gate.check_row(row, 'tuning')
                f.write(json.dumps(row, sort_keys=True)+'\n')
    gate.read_manifest(out/'b2_manifest.jsonl')
    gate.read_manifest(out/'tuning_manifest.jsonl', 'tuning')
    write_json(out/'MANIFEST_REPORT.json', dict(counts=dict(counts), scenes={k: len(v) for k,v in scenes.items()},
               training_rooms=len(rooms)-len(val), validation_rooms=len(val), tuning_frames=992,
               tuning_scans=len(tuning), tuning_objects=sum(map(len, objects.values())), frames32_scans=len(frame_scenes),
               dropped=dropped, source_pins=source_pins, raster_bytes_read=reader.bytes,
               manifests={p.name:sha256(p) for p in [out/'b2_manifest.jsonl',out/'tuning_manifest.jsonl']},
               provenance=pins, inventory_baseline=dict(frames=8000,scenes=250),
               image_hash_status='Upstream pinned RGB hashes; headers checked, no full RGB rehash in O1'))


if __name__ == '__main__':
    main()
