import argparse
from collections import defaultdict
from fractions import Fraction
import math
from pathlib import Path

from .blocking import benchmark_blocking, overlap
from .conventions import FAMILIES
from .generate import counts, sources, write_dataset
from .io import canonical, digest, new_output, pin, read_json, read_jsonl, source_commit, verify_pin, write_json
from .split import PUBLISHED, load_split
from .targets import validate_student_input, validate_target


COMPACT = Path('/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/diagnostic_set_compact_interim_20260922T0325Z_full')


def contained_pin(root, path, sha256):
    path = Path(path)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('dataset source path escapes its declared directory')
    verify_pin({'path': str(path), 'sha256': sha256})
    return pin(path)


def compact_rows(directory):
    directory = Path(directory).resolve()
    index_path = directory / 'candidate_index.jsonl'
    source_pins = [pin(index_path), pin(directory / 'MANIFEST.json')]
    rows, seen = [], set()
    for entry in read_jsonl(index_path):
        if entry['qid'] in seen:
            raise ValueError('duplicate compact candidate qid')
        seen.add(entry['qid'])
        row_pin = contained_pin(directory, entry['row_path'], entry['row_sha256'])
        target_pin = contained_pin(directory, entry['target_path'], entry['sha256'])
        row = read_json(row_pin['path'])
        if any(row[key] != entry[key] for key in ('qid', 'dataset', 'scene')) or row['category'] != entry['question_type']:
            raise ValueError('compact index/row identity mismatch')
        if row['target'] != Path(target_pin['path']).read_text():
            raise ValueError('compact target bytes differ from their authenticated row')
        validate_student_input(row['student_input'])
        rows.append(row)
        source_pins.extend([row_pin, target_pin])
    return rows, source_pins


def measurement_rows(directory):
    directory = Path(directory).resolve()
    manifest = read_json(directory / 'MANIFEST.json')
    if manifest.get('schema') != 'gtmeasure-manifest-v1' or manifest.get('source') != 'gtmeasure_v1':
        raise ValueError('unsupported measurement dataset manifest')
    if digest(manifest['config']) != manifest['config_sha256']:
        raise ValueError('measurement config digest mismatch')
    source_pins = [pin(directory / 'MANIFEST.json')]
    for name, spec in manifest['artifacts'].items():
        if Path(spec['path']).resolve() != directory / name:
            raise ValueError('measurement artifact path mismatch')
        verify_pin(spec)
        source_pins.append(pin(spec['path']))
    if not {'train.jsonl', 'heldout.jsonl', 'split.json', 'CONVENTIONS.json', 'COVERAGE.json', 'CONFIG.json'} <= set(manifest['artifacts']):
        raise ValueError('measurement manifest is missing required artifacts')
    sides = {}
    seen = set()
    for side in ('train', 'heldout'):
        rows = list(read_jsonl(directory / (side + '.jsonl')))
        for row in rows:
            if row['qid'] in seen or row.get('source') != 'gtmeasure_v1' or row.get('family') not in FAMILIES:
                raise ValueError('duplicate or foreign measurement row')
            seen.add(row['qid'])
            if row.get('generation_commit') != manifest['repo_commit'] or row.get('config_sha256') != manifest['config_sha256']:
                raise ValueError('measurement row provenance differs from its manifest')
            validate_student_input(row['student_input'])
            validate_target(row['target'])
        if counts(rows) != manifest['counts'][side]:
            raise ValueError('measurement row census differs from its manifest')
        sides[side] = rows
    record = read_json(directory / 'split.json')
    if [row['qid'] for row in sides['train']] != record['train_qids'] or [row['qid'] for row in sides['heldout']] != record['heldout_qids']:
        raise ValueError('measurement split qids differ from row files')
    return sides, manifest, record, source_pins


def stratified(rows, size, seed, source):
    if type(size) is not int or not 0 <= size <= len(rows):
        raise ValueError('stratified sample size exceeds the available rows')
    groups = defaultdict(list)
    for row in rows:
        groups[row.get('family', row['category'])].append(row)
    for family in groups:
        groups[family].sort(key=lambda row: digest([seed, source, row['qid']]))
    selected, offsets = [], defaultdict(int)
    while len(selected) < size:
        for family in sorted(groups):
            offset = offsets[family]
            if offset < len(groups[family]) and len(selected) < size:
                selected.append(groups[family][offset])
                offsets[family] += 1
    return selected


def mix_training(compact, measurements, ratio, seed=17):
    if not isinstance(ratio, (int, float)) or not math.isfinite(ratio) or not 0 <= ratio <= 1:
        raise ValueError('ratio must be a finite GT fraction in [0, 1]')
    if ratio == 0:
        base_size, gt_size = len(compact), 0
    elif ratio == 1:
        base_size, gt_size = 0, len(measurements)
    else:
        value = Fraction(str(ratio))
        base_size = min(len(compact), int(len(measurements) * (1 - value) / value))
        gt_size = min(len(measurements), round(base_size * value / (1 - value)))
        if not base_size or not gt_size:
            raise ValueError('requested ratio needs at least one training row from each source')
    rows = stratified(compact, base_size, seed, 'compact') + stratified(measurements, gt_size, seed, 'gtmeasure_v1')
    rows.sort(key=lambda row: digest([seed, 'mixed-order', row['qid']]))
    if len({row['qid'] for row in rows}) != len(rows):
        raise ValueError('mixing would duplicate a training qid')
    return rows, {'requested_gt_fraction': ratio, 'actual_gt_fraction': gt_size / len(rows) if rows else 0,
                  'rule': 'largest feasible mixture without replacement; downsample the overrepresented source; round GT row count to nearest integer',
                  'available': {'compact': len(compact), 'gtmeasure_v1': len(measurements)},
                  'selected': {'compact': base_size, 'gtmeasure_v1': gt_size},
                  'excluded_by_ratio': {'compact': len(compact) - base_size, 'gtmeasure_v1': len(measurements) - gt_size}}


def mix_rows(compact, measurements, policy, ratio, seed=17):
    all_rows = [*compact, *measurements]
    if len({row['qid'] for row in all_rows}) != len(all_rows):
        raise ValueError('source datasets contain duplicate qids')
    compact_train, compact_heldout = policy.partition(compact)
    gt_train, gt_heldout = policy.partition(measurements)
    train, selection = mix_training(compact_train, gt_train, ratio, seed)
    heldout = sorted([*compact_heldout, *gt_heldout], key=lambda row: row['qid'])
    policy.assert_train(train)
    record = policy.record(train, heldout)
    return train, heldout, record, selection


def run(args):
    commit = source_commit()
    policy = load_split(args.split)
    compact, compact_pins = compact_rows(args.compact_dir)
    sides, gt_manifest, gt_split, gt_pins = measurement_rows(args.gtmeasure_dir)
    if gt_split['inherited_split'] != policy.inherited_pin:
        raise ValueError('measurement data and compact data inherit different arm C split pins')
    for row in sides['heldout']:
        if policy.side(row['dataset'], row['scene']) != 'heldout':
            raise ValueError('published mixer split would move a measurement holdout into training')
    train, heldout, record, selection = mix_rows(compact, [*sides['train'], *sides['heldout']], policy, args.ratio, args.seed)
    evaluation, _ = benchmark_blocking(gt_manifest['benchmark_blocking'])
    overlap_census = overlap([{'dataset': row['dataset'], 'scene_name': row['scene']} for row in [*train, *heldout]], evaluation)
    if overlap_census['any']:
        raise ValueError('benchmark scene group reached the mixed dataset')
    output = new_output(args.output)
    artifacts = write_dataset(output, train, heldout, record)
    source_pins = [*compact_pins, *gt_pins, pin(args.split), policy.inherited_pin]
    by_path = {spec['path']: spec for spec in source_pins}
    config = {'seed': args.seed, 'ratio': args.ratio, 'selection': selection['rule'],
              'split_seed': 17, 'source_sha256': digest(sources())}
    report = {'schema': 'gtmeasure-mixed-manifest-v1', 'repo_commit': commit, 'config': config, 'config_sha256': digest(config),
              'source_files': sources(), 'source_paths': sorted(by_path.values(), key=lambda value: value['path']),
              'source_datasets': {'compact': str(args.compact_dir.resolve()), 'gtmeasure': str(args.gtmeasure_dir.resolve())},
              'counts': {'train': counts(train), 'heldout': counts(heldout)}, 'selection': selection,
              'split_census': record['counts'], 'benchmark_blocking': gt_manifest['benchmark_blocking'], 'overlap': overlap_census,
              'inherited_split': policy.inherited_pin, 'artifacts': artifacts,
              'independent_review': 'pending; mixed JSONL rows do not grant trainer admission'}
    write_json(output / 'MANIFEST.json', report)
    print(canonical({'counts': report['counts'], 'selection': selection, 'split': record['counts']}), flush=True)
    return 0 if train else 2


def main():
    parser = argparse.ArgumentParser(description='Mix compact and measurement rows without heldout-scene leakage or duplicate sampling.')
    parser.add_argument('--compact-dir', type=Path, default=COMPACT)
    parser.add_argument('--split', type=Path, default=PUBLISHED)
    parser.add_argument('--gtmeasure-dir', type=Path, required=True)
    parser.add_argument('--ratio', type=float, required=True, help='Fraction of final training rows from gtmeasure, in [0,1]; no replacement.')
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--output', type=Path, required=True)
    return run(parser.parse_args())


if __name__ == '__main__':
    raise SystemExit(main())
