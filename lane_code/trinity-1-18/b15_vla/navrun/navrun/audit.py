"""Scene overlap checks. Unknown model provenance is never treated as no overlap."""
import argparse
from pathlib import Path
from .episodes import canonical_scene, load_split
from .io import read_json, write_json

def scene_set(items):
    return {canonical_scene(x.scene_id if hasattr(x, 'scene_id') else x) for x in items}

def split_audit(train, unseen, test):
    t, v, s = map(scene_set, (train, unseen, test))
    overlap = {'train_val_unseen': sorted(t & v), 'train_test': sorted(t & s),
               'val_unseen_test': sorted(v & s)}
    result = dict(scene_counts=dict(train=len(t), val_unseen=len(v), test=len(s)), overlap=overlap)
    if any(overlap.values()):
        raise ValueError('Scene leakage: ' + str(overlap))
    return result

def manifest_scenes(path):
    d = read_json(path)
    if isinstance(d, dict):
        d = d.get('scenes', d.get('episodes', d.get('rows')))
    if not isinstance(d, list):
        raise ValueError('Manifest must contain scenes, episodes or rows')
    return scene_set([x.get('scene_id', x.get('scene')) if isinstance(x, dict) else x for x in d])

def audit_manifests(episodes, manifests):
    evaluation = scene_set(episodes)
    details, excluded = {}, set()
    for name in ('student', 'g3t', 'sam3'):
        path = manifests.get(name)
        if not path or not Path(path).is_file():
            details[name] = dict(status='provenance unknown', overlap=[])
        else:
            shared = evaluation & manifest_scenes(path)
            excluded |= shared
            details[name] = dict(status='audited', overlap=sorted(shared), path=str(path))
    return dict(models=details, excluded_scenes=sorted(excluded),
                retained_ids=[e.episode_id for e in episodes if canonical_scene(e.scene_id) not in excluded])

def main():
    p = argparse.ArgumentParser()
    for name in ('student', 'g3t', 'sam3', 'output'):
        p.add_argument('--' + name)
    a = p.parse_args()
    result = split_audit(load_split('train'), load_split('val_unseen'), load_split('test'))
    result['provenance'] = audit_manifests(load_split('val_unseen'), vars(a))
    if a.output:
        write_json(a.output, result)
    print(result)

if __name__ == '__main__':
    main()
