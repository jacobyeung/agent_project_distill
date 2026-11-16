"""Pinned reference executor and routed-read command line."""
from student_pilot.r2_policy import unsupported_entry
unsupported_entry('rk/programs.py:import')
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

import numpy as np

REFERENCE = Path('/scratch/jjyeung/orch_cd/evalx/work/tp/programs.py')
_spec = importlib.util.spec_from_file_location('_rkit_reference_programs', REFERENCE)
_reference = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_reference)
Scene, GTGround = _reference.Scene, _reference.GTGround
HeadSource, PerFrameHeadSource = _reference.HeadSource, _reference.PerFrameHeadSource
load_heads, run_vsi = _reference.load_heads, _reference.run_vsi
closest_sets, fit_gbox, robust, T = (_reference.closest_sets, _reference.fit_gbox,
                                  _reference.robust, _reference.T)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def code_pins():
    files = [Path(__file__).with_name(n+'.py') for n in
             ('sets', 'ground', 'scheme', 'revsi', 'programs', 'report', 'gtmask')]
    files += [REFERENCE, Path(T.__file__), Path(os.environ.get('RK_MDG_ROOT', '/scratch/jjyeung/orch_cd/mdg_next/work/c1mix_mdg_ro'))/'student_pilot/mdg_eval.py']
    pins = {str(p): sha256(p) for p in files}
    return pins, hashlib.sha256(json.dumps(pins, sort_keys=True).encode()).hexdigest()


def assert_frame_indices(heads, expected):
    with np.load(heads, allow_pickle=False) as z:
        key = 'anchor_frame_indices' if 'anchor_frame_indices' in z else 'frame_indices'
        if key not in z:
            raise ValueError(f'Heads missing frame indices: {heads}')
        actual = z[key]
        if not np.array_equal(actual, np.asarray(expected)):
            raise ValueError(f'Frame-index mismatch between heads and export: {heads}')
        if 'anchor_frame_indices' in z and 'frame_indices' in z:
            if not np.array_equal(z['frame_indices'], expected):
                raise ValueError(f'Conflicting heads frame indices: {heads}')


def assert_export_frames(export, audit, expected):
    if expected is None or np.asarray(expected).shape != (32,):
        raise ValueError('Export index missing 32 frame indices')
    found = []
    def visit(value):
        if isinstance(value, dict):
            for name, child in value.items():
                if name in ('frame_indices', 'anchor_frame_indices'):
                    found.append(child)
                elif isinstance(child, dict):
                    visit(child)
    visit(audit)
    with np.load(export, allow_pickle=False) as z:
        found.extend(z[k] for k in ('frame_indices', 'anchor_frame_indices') if k in z)
    if not found:
        raise ValueError('MDG export missing frame indices')
    if any(not np.array_equal(value, expected) for value in found):
        raise ValueError('Frame-index mismatch between MDG audit/export and export index')


def head_sources(heads):
    with np.load(heads, allow_pickle=False) as z:
        result = {}
        for name in ('gravity_source', 'pose_source', 'depth_source', 'fov_source'):
            value = z[name].item() if name in z else None
            result[name] = value.decode() if isinstance(value, bytes) else value
        return result


def scene_key(dataset, scene):
    ds = re.sub('[^a-z0-9]', '', dataset.lower().replace('++', 'pp'))
    ds = {'scannetv2': 'scannet', 'scannetppv2': 'scannetpp'}.get(ds, ds)
    if ds not in {'scannet', 'scannetpp', 'arkitscenes', '3rscan', 'multiscan'}:
        raise ValueError('Unknown dataset: '+dataset)
    if not re.fullmatch(r'[A-Za-z0-9_-]+', scene):
        raise ValueError('Invalid scene: '+scene)
    return f'{ds}/{scene}'


def read_index(directory):
    root = Path(directory)
    path = root/'INDEX.json'
    if not path.exists():
        root, path = root/'export', root/'export/INDEX.json'
    raw = json.loads(path.read_text())
    entries = raw.get('selections', raw.get('entries', raw))
    if isinstance(entries, list):
        entries = {str(i): e for i, e in enumerate(entries)}
    by_scene = {}
    for selection, entry in entries.items():
        key = entry.get('scene_key', entry.get('scene'))
        if key in by_scene:
            raise ValueError(f'Multiple selections for scene {key}; select a unique export')
        by_scene[key] = dict(entry, selection=selection)
    return root, by_scene


def run(args):
    from .ground import MaskGround
    from .scheme import V311Scene
    from . import sets
    root, entries = read_index(args.mdg_export)
    items = sets.dev_items() if args.set == 'dev' else sets.revsi_items()
    scenes = set(args.scenes.split(',')) if args.scenes else None
    counts, grouped = Counter(), defaultdict(list)
    for item in items:
        key = scene_key(item['dataset'], item['scene'])
        if scenes and item['scene'] not in scenes and key not in scenes:
            continue
        if args.limit_per_type is not None and counts[item['type']] >= args.limit_per_type:
            continue
        counts[item['type']] += 1
        grouped[key].append(item)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows, npz_pins, oracle, sources = [], {}, False, {}
    for key, group in sorted(grouped.items()):
        sources[key] = dict.fromkeys(('gravity_source', 'pose_source', 'depth_source', 'fov_source'))
        entry = entries.get(key)
        if entry is None:
            rows.extend(dict(qid=i['qid'], set=args.set, type=i['type'], scene=key,
                             pred=None, refusal='no_export', trace=[]) for i in group)
            continue
        export = root/entry['npz']
        heads = Path(args.heads)/(key.replace('/', '__')+'.npz')
        ground = MaskGround(export)
        is_oracle = bool(ground.audit.get('gt_substitution', False))
        if is_oracle and not args.allow_gt_substitution:
            raise ValueError('GT substitution requires --allow-gt-substitution')
        oracle |= is_oracle
        expected = entry.get('frame_indices')
        assert_export_frames(export, ground.audit, expected)
        npz_pins[str(export.resolve())] = sha256(export)
        if not heads.exists():
            rows.extend(dict(qid=i['qid'], set=args.set, type=i['type'], scene=key,
                             pred=None, refusal='no_frame: missing_heads', trace=[],
                             gt_substitution=is_oracle) for i in group)
            continue
        assert_frame_indices(heads, expected)
        sources[key] = head_sources(heads)
        is_oracle |= any(value == 'gt' for value in sources[key].values())
        if is_oracle and not args.allow_gt_substitution:
            raise ValueError('GT substitution requires --allow-gt-substitution (geometry sources)')
        oracle |= is_oracle
        npz_pins[str(heads.resolve())] = sha256(heads)
        geo = load_heads(heads)
        if not isinstance(geo, PerFrameHeadSource):
            raise ValueError('Routed reads require per_frame heads')
        scene = V311Scene(geo, ground, gates=getattr(args, 'gates', False))
        for item in group:
            pred, reason = scene.run(item)
            if isinstance(pred, np.generic):
                pred = pred.item()
            rows.append(dict(qid=item['qid'], set=args.set, type=item['type'], scene=key,
                             pred=pred, refusal=reason, trace=list(scene.trace),
                             gt_substitution=is_oracle))
    code, code_sha = code_pins()
    with (out/f'routed_{args.set}.jsonl').open('w') as stream:
        for row in rows:
            stream.write(json.dumps(row, allow_nan=False)+'\n')
    metadata = dict(set=args.set, n=len(rows), gt_substitution=oracle, code_sha=code_sha,
                    code_pins=code, npz_pins=npz_pins, index_sha256=sha256(root/'INDEX.json'),
                    command=sys.argv, counts=dict(counts), geometry_sources=sources,
                    gates=getattr(args, 'gates', False))
    (out/'RUN.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(json.dumps(dict(n=len(rows), refusals=sum(r['pred'] is None for r in rows), oracle=oracle)))
    return rows


def main():
    parser = argparse.ArgumentParser(__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('run')
    p.add_argument('--set', choices=['dev', 'revsi'], required=True)
    p.add_argument('--mdg-export', required=True)
    p.add_argument('--heads', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--scenes')
    p.add_argument('--limit-per-type', type=int)
    p.add_argument('--allow-gt-substitution', action='store_true')
    p.add_argument('--gates', action='store_true', help='Secondary row: SPEC section-9 near-tie, short-vector and near-boundary refusals on own values')
    run(parser.parse_args())


if __name__ == '__main__':
    main()
