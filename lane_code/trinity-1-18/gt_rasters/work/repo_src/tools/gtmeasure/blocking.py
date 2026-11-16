# Copied from tools/vstigen/blocking.py at e2f387e (vstigen-membership-v4-20260922).
import re
from pathlib import Path

from .io import read_json, sha


BLOCKING_RULE = ('build_membership_v2.py:38-42 scene_key() then :87-89; ScanNet '
                 'sceneNNNN_XX -> sceneNNNN, scannetppv2/scannetpp2 -> scannetpp.')
EXPECTED_GROUPS = {'vsibench_full': 288, 'vstibench_full': 142, 'revsi_full': 380}


def scene_key(source, scene):
    source = {'scannetppv2': 'scannetpp', 'scannetpp2': 'scannetpp'}.get(source, source)
    if source == 'scannet':
        scene = re.sub(r'_\d+$', '', scene)
    return source, scene


def benchmark_blocking(specs):
    if set(specs) != {'vsibench_full', 'vstibench_full', 'revsi_full'}:
        raise ValueError('all three benchmark authorities are required')
    evaluation, blocked = {}, set()
    for name, expected in sorted(specs.items()):
        if expected['scene_groups'] != EXPECTED_GROUPS[name]:
            raise ValueError(f'required benchmark group census drift: {name}')
        path = Path(expected['path'])
        measured_sha = sha(path)
        if measured_sha != expected['sha256']:
            raise ValueError(f'benchmark authority digest mismatch: {name}')
        rows = read_json(path)
        keys = {scene_key(row.get('revsi_source_corpus', row['dataset']), row['scene_name']) for row in rows}
        if len(rows) != expected['rows'] or len(keys) != expected['scene_groups']:
            raise ValueError(f'benchmark authority census mismatch: {name}')
        evaluation[name] = {'path': str(path), 'sha256': measured_sha, 'rows': len(rows),
                            'scene_groups': len(keys), 'keys': keys}
        blocked.update(keys)
    return evaluation, blocked


def overlap(rows, evaluation):
    blocked = set().union(*(info['keys'] for info in evaluation.values()))
    return {'by_benchmark': {name: sum(scene_key(row['dataset'], row['scene_name']) in info['keys'] for row in rows)
                             for name, info in evaluation.items()},
            'any': sum(scene_key(row['dataset'], row['scene_name']) in blocked for row in rows)}


def refuse_blocked(dataset, scene, blocked):
    if scene_key(dataset, scene) in blocked:
        raise ValueError('benchmark_scene_group_blocked')
