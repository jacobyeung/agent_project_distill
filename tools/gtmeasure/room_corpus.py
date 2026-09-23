"""Rebuild a sealed corpus by replaying only its room rows against authenticated labels."""
import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import json
from pathlib import Path

from .generate import counts, sources
from .io import canonical, digest, new_output, pin, read_json, sha, source_commit, verify_pin, write_json
from .questions import rewrite_room_row
from .room_labels import POLICY, RoomLabelDeferred
from .room_repair import RoomRepair


def repair_sources(structure):
    root = Path(__file__).resolve().parents[2]
    return {**sources(structure), **{name: sha(root / name) for name in
            ('tools/gtmeasure/room_corpus.py', 'tools/gtmeasure/room_repair.py', 'tools/gtmeasure/verify.py')}}


def repair_config(repair, source):
    return {**repair.manifest['config'], 'conventions_sha256': digest(repair.conventions),
            'room_label_policy': POLICY, 'selective_room_repair': source,
            'source_sha256': digest(repair_sources(repair.manifest['config'].get('structure', 'v1'))),
            'selection': 'retain source qids and sides; rewrite room rows only; retain non-room bytes'}


def replay(repair, source, commit):
    """Return original raw non-room lines and corrected room lines, with explicit deferrals."""
    config = repair_config(repair, source)
    sides, deferred, hashes = {}, [], {}
    for side in ('train', 'heldout'):
        lines, original_nonroom, rebuilt_nonroom = [], hashlib.sha256(), hashlib.sha256()
        with (Path(source['path']).parent / (side + '.jsonl')).open('rb') as handle:
            for raw in handle:
                row = json.loads(raw)
                if row['family'] != 'gtm_room_size':
                    original_nonroom.update(raw)
                    rebuilt_nonroom.update(raw)
                    lines.append(raw)
                    continue
                try:
                    if side != 'train':
                        raise RoomLabelDeferred('room_label_not_training')
                    result = rewrite_room_row(row, repair.conventions, repair.labels, commit=commit,
                                              config_sha=digest(config), structure=config.get('structure', 'v1'))
                except ValueError as error:
                    reason = str(error)
                    if not isinstance(error, RoomLabelDeferred) and reason != 'rounding_midpoint_not_specified_by_authority':
                        raise
                    deferred.append({'qid': row['qid'], 'dataset': row['dataset'], 'scene': row['scene'],
                                     'side': side, 'reason': reason})
                    continue
                lines.append((canonical(result) + '\n').encode())
        sides[side] = lines
        hashes[side] = {'source': original_nonroom.hexdigest(), 'rebuilt': rebuilt_nonroom.hexdigest()}
    return sides, deferred, hashes


def verify_selective_rows(directory, manifest):
    source = manifest['config']['selective_room_repair']
    parent = read_json(verify_pin(source))
    if parent['config'].get('selective_room_repair'):
        raise ValueError('selective room repair requires an original generation corpus')
    repair = RoomRepair(source)
    if manifest['config'] != repair_config(repair, source):
        raise ValueError('selective repair config does not replay')
    if read_json(directory / 'CONVENTIONS.json') != repair.conventions:
        raise ValueError('selective repair conventions do not replay')
    sides, deferred, hashes = replay(repair, source, manifest['repo_commit'])
    for side, lines in sides.items():
        if (directory / (side + '.jsonl')).read_bytes() != b''.join(lines):
            raise ValueError('selective repair changed preserved bytes or room replay: ' + side)
    if read_json(directory / 'ROOM_REPAIR.json') != {'source_manifest': source, 'deferred': deferred, 'nonroom_sha256': hashes}:
        raise ValueError('selective repair deferrals or preservation hashes do not replay')


def run(source_directory, output):
    commit = source_commit()
    source = pin(source_directory / 'MANIFEST.json')
    repair = RoomRepair(source)
    config = repair_config(repair, source)
    raw_sides, deferred, hashes = replay(repair, source, commit)
    sides = {side: [json.loads(raw) for raw in lines] for side, lines in raw_sides.items()}
    output = new_output(output)
    artifacts = {}
    for side, lines in raw_sides.items():
        name = side + '.jsonl'
        with (output / name).open('xb') as handle:
            handle.writelines(lines)
        artifacts[name] = pin(output / name, len(lines))
    split = repair.policy.record(sides['train'], sides['heldout'])
    write_json(output / 'split.json', split)
    write_json(output / 'CONVENTIONS.json', repair.conventions)
    write_json(output / 'CONFIG.json', {'repo_commit': commit, 'config': config, 'config_sha256': digest(config)})
    write_json(output / 'ROOM_REPAIR.json', {'source_manifest': source, 'deferred': deferred, 'nonroom_sha256': hashes})
    by_scene = defaultdict(list)
    for lines in raw_sides.values():
        for raw in lines:
            row = json.loads(raw)
            by_scene[row['dataset'], row['scene']].append(raw)
    coverage = copy.deepcopy(read_json(source_directory / 'COVERAGE.json'))
    for entry in coverage['scenes']:
        if entry['status'] == 'not_requested':
            continue
        key = entry['dataset'], entry['scene_name']
        lines = sorted(by_scene[key], key=lambda raw: json.loads(raw)['qid'])
        entry.pop('checkpoint', None)
        entry['rows'] = len(lines)
        entry['by_family'] = dict(Counter(json.loads(raw)['family'] for raw in lines))
        entry['room_repair_deferrals'] = [r for r in deferred if (r['dataset'], r['scene']) == key]
        entry.pop('same_seed_repeat_byte_identical', None)
        checkpoint = output / 'scene_checkpoints' / '__'.join(key)
        checkpoint.mkdir(parents=True)
        with (checkpoint / 'rows.jsonl').open('xb') as handle:
            handle.writelines(lines)
        write_json(checkpoint / 'COVERAGE.json', entry)
        entry['checkpoint'] = {'rows': pin(checkpoint / 'rows.jsonl', len(lines)), 'coverage': pin(checkpoint / 'COVERAGE.json')}
    write_json(output / 'COVERAGE.json', coverage)
    for name in ('split.json', 'CONVENTIONS.json', 'CONFIG.json', 'COVERAGE.json', 'ROOM_REPAIR.json'):
        artifacts[name] = pin(output / name)
    manifest = copy.deepcopy(repair.manifest)
    manifest.pop('assembly', None)
    manifest.update(repo_commit=commit, config=config, config_sha256=digest(config), source_files=repair_sources(config.get('structure', 'v1')),
                    artifacts=artifacts, counts={**{side: counts(rows) for side, rows in sides.items()},
                                               'all': counts(sides['train'] + sides['heldout'])},
                    split_census=split['counts'], determinism={'method': 'authenticated selective replay; exact non-room byte preservation'},
                    selective_repair_source=source)
    write_json(output / 'MANIFEST.json', manifest)
    verify_selective_rows(output, manifest)
    print(canonical({'counts': manifest['counts'], 'deferred': dict(Counter(r['reason'] for r in deferred)),
                     'nonroom_sha256': hashes}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.source.resolve(), args.output)


if __name__ == '__main__':
    main()
