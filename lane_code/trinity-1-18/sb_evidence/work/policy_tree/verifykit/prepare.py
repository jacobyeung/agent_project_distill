"""Prepare reference-only candidate manifests; GT labels are separate artifacts."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image
from .io import ROOT, RAW, GT, INDEX, FRAMES, cache, tower, dump, rows, write_rows, sha, module, mask_for, validate


def mdg_presence(root, scene, name):
    path = Path(root)/(scene.replace('/', '__')+'.npz')
    with np.load(path, allow_pickle=False) as z:
        names = z['names'].tolist()
        norm = ' '.join(name.lower().replace('_', ' ').split())
        return z['prob'][names.index(norm)].astype(float).tolist()


def prepare_dev(out, scenes=None, presence_root=None):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('verifykit/prepare.py:prepare_dev')
    index = json.loads(INDEX.read_text())
    groups, pins = [], {str(INDEX): sha(INDEX)}
    for scene, entry in sorted(index.items()):
        if scenes and scene not in scenes and scene.split('/')[-1] not in scenes:
            continue
        path = RAW/(scene.replace('/', '__')+'.npz')
        data = cache(str(path))
        pins[str(path)] = sha(path)
        with np.load(INDEX.parent/entry['npz'], allow_pickle=False) as z:
            names = z['names'].tolist()
        for name in names:
            phrase = tower().phrase(name)
            prior = mdg_presence(presence_root, scene, name) if presence_root else None
            candidates = []
            for slot in range(32):
                record = data['frames'][str(slot)]['phrases'][phrase]
                ranked = sorted(enumerate(record['instances']), key=lambda x: (-x[1]['score'], x[0]))[:5]
                for j, inst in ranked:
                    if not any(inst['mask']['counts'][1::2]):
                        continue
                    score, pres = float(inst['score']), float(record['presence'])
                    ref = dict(path=str(path), phrase=phrase, slot=slot, instance_index=j)
                    candidates.append(dict(candidate_id=f'f{slot:02d}-i{j}', slot=slot, mask_ref=ref,
                        peak=score*pres, presence=float(prior[slot]) if prior is not None else pres,
                        support=1., exclusivity_margin=0., members=[dict(slot=slot, mask_ref=ref)]))
            group = dict(schema='verify-candidates-v1', object_id=scene+'::'+name, scene=scene, name=name,
                frame_indices=entry['frame_indices'], frames_root=str(FRAMES), candidates=candidates,
                candidate_source='cached_top5_per_frame_UNLINKED',
                presence_source='mdg' if prior is not None else 'sam3_presence', oracle=False)
            if prior is not None:
                group['v3_slots'] = sorted(range(32), key=lambda k: (-prior[k], k))[:4]
                group['v3_presence_source'] = 'mdg'
            groups.append(group)
    validate(groups)
    write_rows(out, groups)
    counts = call_counts(groups)
    dump(str(out)+'.meta.json', dict(source_sha256=pins, counts=counts,
        caveat='Unlinked per-frame candidates are for build tests; use E1 linked top-K for the E2 decision.'))
    return counts


def call_counts(groups):
    return dict(objects=len(groups), scenes=len({g['scene'] for g in groups}),
        V1=sum(len(g['candidates']) for g in groups),
        V2=sum((len(g['candidates'])+4)//5 for g in groups),
        V3=sum(len(g.get('v3_slots', [])) for g in groups),
        V3_missing_presence=sum('v3_slots' not in g for g in groups))


def tplib():
    return module('_verify_tplib', ROOT/'toolprog/work/tp/tplib.py')


def label_candidates(candidates_path, out, add_oracle_v3=None, split='all', split_file=None):
    groups = rows(candidates_path)
    if split != 'all':
        from .io import SPLIT
        tuning = set(json.loads(Path(split_file or SPLIT).read_text())['tuning_scenes'])
        groups = [g for g in groups if (g['scene'] in tuning) == (split == 'tuning')]
    by_scene = defaultdict(list)
    for g in groups:
        by_scene[g['scene']].append(g)
    labels = []
    T = tplib()
    for scene, scene_groups in sorted(by_scene.items()):
        path = GT/(scene.split('/')[-1]+'.npz')
        with np.load(path, allow_pickle=False) as z:
            inst, ids, names, valid, indices = z['inst'], z['ids'], z['labels'].tolist(), z['valid'], z['frame_indices']
        gt_sha = sha(path)
        for g in scene_groups:
            if list(indices) != g['frame_indices']:
                raise ValueError('GT frame indices differ')
            matches = T.match_labels(g['name'], names)
            target = np.zeros_like(inst, dtype=bool)
            for instance in [i for i, n in zip(ids, names) if n in matches]:
                m = inst == instance
                target |= m & (m.sum(axis=(1, 2)) >= 154)[:, None, None]
            target &= valid[:, None, None]
            visibility = target.any(axis=(1, 2))
            truth = {}
            for c in g['candidates']:
                m = mask_for(c)
                native = np.asarray(Image.fromarray(target[c['slot']]).resize((640, 480), Image.Resampling.NEAREST), bool)
                click = tower().deepest(m)
                x, y = (min(639, int(click[0]*640/1000)), min(479, int(click[1]*480/1000))) if click else (0, 0)
                truth[c['candidate_id']] = dict(on_target=bool(click and native[y, x]),
                    iou=float((m & native).sum()/max(1, (m | native).sum())))
            label = dict(object_id=g['object_id'], scene=scene, candidates=truth,
                         absent=bool(not visibility[g['pointing_slot']]) if 'pointing_slot' in g else not bool(visibility.any()),
                         frame_presence=visibility.tolist(), gt_sha256=gt_sha)
            labels.append(label)
            if add_oracle_v3 and 'v3_slots' not in g:
                g['v3_slots'] = sorted(range(32), key=lambda k: (-int(visibility[k]), k))[:4]
                g['v3_presence_source'] = 'GT_PRESENCE_ORACLE'
    write_rows(out, labels)
    if add_oracle_v3:
        write_rows(add_oracle_v3, groups)
    return dict(objects=len(labels), absent=sum(x['absent'] for x in labels))


def prepare_pointing(out, membership, scenes=None):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('verifykit/prepare.py:prepare_pointing')
    items = json.loads(Path(membership).read_text())['items']
    T = tplib()
    grouped = defaultdict(list)
    for it in items:
        if not scenes or it['scene'] in scenes or it['scene'].split('/')[-1] in scenes:
            grouped[it['scene']].append(it)
    result = []
    for scene, items in sorted(grouped.items()):
        path = GT/(scene.split('/')[-1]+'.npz')
        with np.load(path, allow_pickle=False) as z:
            inst, ids, valid, indices = z['inst'], set(map(int, z['ids'])), z['valid'], z['frame_indices'].tolist()
        for it in items:
            slot = int(it['frame'])-1
            if indices != it['frame_indices']:
                raise ValueError('Pointing anchor mismatch')
            candidates = []
            # All visible annotated instances, independent of the queried name.
            for instance in sorted(set(map(int, np.unique(inst[slot]))) & ids):
                if not valid[slot] or int((inst[slot] == instance).sum()) < 154:
                    continue
                ref = dict(kind='gt_instance', path=str(path), slot=slot, instance_id=instance)
                candidates.append(dict(candidate_id=f'gt{instance}', slot=slot, mask_ref=ref,
                    peak=.5, presence=.5, support=1., exclusivity_margin=0., members=[dict(slot=slot, mask_ref=ref)]))
            result.append(dict(schema='verify-candidates-v1', object_id=it['id'], scene=scene, name=it['obj'],
                frame_indices=indices, frames_root=str(FRAMES), candidates=candidates,
                pointing_slot=slot, candidate_source='GT_INSTANCES_ORACLE', presence_source='constant',
                oracle=True, v3_slots=[slot], v3_presence_source='pointing_fixed_frame'))
    write_rows(out, validate(result))
    return call_counts(result)


def main():
    p = argparse.ArgumentParser(__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    d = sub.add_parser('dev'); d.add_argument('--out', required=True); d.add_argument('--scenes'); d.add_argument('--presence-root')
    d = sub.add_parser('pointing'); d.add_argument('--out', required=True); d.add_argument('--scenes')
    d.add_argument('--membership', default=str(ROOT/'evalx/work/aws_vl/inputs/pointing_membership.json'))
    d = sub.add_parser('labels'); d.add_argument('--candidates', required=True); d.add_argument('--out', required=True)
    d.add_argument('--oracle-v3-out')
    d.add_argument('--split', choices=['all', 'tuning', 'heldout'], default='all')
    d.add_argument('--split-file')
    d = sub.add_parser('counts'); d.add_argument('--candidates', required=True)
    a = p.parse_args()
    if a.command == 'dev': r = prepare_dev(a.out, set(a.scenes.split(',')) if a.scenes else None, a.presence_root)
    elif a.command == 'pointing': r = prepare_pointing(a.out, a.membership, set(a.scenes.split(',')) if a.scenes else None)
    elif a.command == 'labels': r = label_candidates(a.candidates, a.out, a.oracle_v3_out, a.split, a.split_file)
    else: r = call_counts(rows(a.candidates))
    print(json.dumps(r))

if __name__ == '__main__': main()
