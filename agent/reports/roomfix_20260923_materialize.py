"""Materialize a mixed gtmeasure/compact set into the dataset-builder candidate layout.

Writes <output>/candidate_index.jsonl plus <output>/targets/<qid>/{row.json,target.txt},
the layout student_pilot.provisional:load_provisional_candidates consumes and the arm C
set already uses. Makes no admission or selection decision: every train.jsonl and
heldout.jsonl row becomes exactly one candidate row and one target file, in qid order.
Index-level fields for compact rows are carried through verbatim from their source
candidate index; for gtmeasure rows they are read off the row itself.
"""
import json, shutil, sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKTREE))

from tools.gtmeasure.io import digest, new_output, output_path, pin, read_json, read_jsonl, sha, write_json, write_jsonl  # noqa: E402

PILOT = Path('/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918')
CARRIED = ('answer', 'pool', 'question_type', 'generation_commit', 'validation_commit')


def write_text(path, text):
    with output_path(path).open('x') as handle:
        handle.write(text)


def entry_for(row, source_index, target_path, row_path):
    """Index fields: verbatim from the compact source index, or read off the gtmeasure row."""
    if row['qid'] in source_index:
        entry = {k: v for k, v in source_index[row['qid']].items() if k not in ('row_path', 'target_path', 'row_sha256', 'sha256')}
        origin = 'compact'
    else:
        if row.get('source') != 'gtmeasure_v1':
            raise ValueError('row is neither a compact candidate nor a gtmeasure row: ' + row['qid'])
        entry = {'qid': row['qid'], 'dataset': row['dataset'], 'scene': row['scene'],
                 'question_type': row['category'], 'answer': str(row['ground_truth']['answer']),
                 'pool': row['source'], 'family': row['family'], 'config_sha256': row['config_sha256'],
                 'generation_commit': row['generation_commit'],
                 # gtmeasure generates and validates a row in one pass under one commit
                 'validation_commit': row['generation_commit']}
        origin = 'gtmeasure'
    for key in CARRIED:
        if not str(entry.get(key, '')).strip():
            raise ValueError(f'materialized entry lacks {key}: ' + row['qid'])
    if entry['question_type'] != row['category'] or entry['qid'] != row['qid'] or entry['scene'] != row['scene']:
        raise ValueError('index/row identity drift: ' + row['qid'])
    entry.update({'row_path': str(row_path), 'row_sha256': sha(row_path),
                  'target_path': str(target_path), 'sha256': sha(target_path)})
    return entry, origin


def materialize(name, spec):
    mix, out = spec['mix'], spec['out']
    source_index = {e['qid']: e for e in read_jsonl(spec['compact'] / 'candidate_index.jsonl')}
    sides = {side: list(read_jsonl(mix / (side + '.jsonl'))) for side in ('train', 'heldout')}
    rows = [*sides['train'], *sides['heldout']]
    if len({r['qid'] for r in rows}) != len(rows):
        raise ValueError('duplicate qid across the two sides')

    output = new_output(out)
    targets = output / 'targets'
    targets.mkdir()
    entries, origins = [], {'compact': 0, 'gtmeasure': 0}
    for row in sorted(rows, key=lambda r: r['qid']):
        directory = targets / row['qid']
        directory.mkdir()
        write_text(directory / 'target.txt', row['target'])
        write_json(directory / 'row.json', row)
        entry, origin = entry_for(row, source_index, directory / 'target.txt', directory / 'row.json')
        origins[origin] += 1
        entries.append(entry)
    entries.sort(key=lambda e: e['qid'])
    write_jsonl(output / 'candidate_index.jsonl', entries)
    shutil.copyfile(mix / 'split.json', output / 'split.json')

    tree = digest(sorted((str(p.relative_to(output)), sha(p)) for p in targets.rglob('*') if p.is_file()))
    by_side = {side: {'rows': len(value), 'qids': None} for side, value in sides.items()}
    record = {'schema': 'gtmeasure-mixed-candidate-layout-v1', 'set': name,
              'source_mix': str(mix), 'source_compact_index': str(spec['compact'] / 'candidate_index.jsonl'),
              'counts': {'train': len(sides['train']), 'heldout': len(sides['heldout']),
                         'candidate_index': len(entries), 'targets': origins},
              'reconciliation': {'train_plus_heldout': len(sides['train']) + len(sides['heldout']),
                                 'index_rows': len(entries),
                                 'target_directories': sum(1 for p in targets.iterdir() if p.is_dir())},
              'artifacts': {'candidate_index.jsonl': pin(output / 'candidate_index.jsonl', len(entries)),
                            'split.json': pin(output / 'split.json')},
              'targets_tree_sha256': tree,
              'field_mapping': {
                  'compact': 'index fields carried verbatim from the source candidate index; only the four path/digest pins are rewritten',
                  'gtmeasure_answer': 'row.ground_truth.answer, stringified',
                  'gtmeasure_pool': 'row.source',
                  'gtmeasure_validation_commit': 'row.generation_commit (generated and validated in one pass under one commit)'},
              'independent_review': 'pending; this layout does not grant trainer admission'}
    write_json(output / 'MATERIALIZATION.json', record)
    print(json.dumps({'set': name, 'output': str(output), 'counts': record['counts'],
                      'reconciliation': record['reconciliation'],
                      'candidate_index_sha256': record['artifacts']['candidate_index.jsonl']['sha256'],
                      'targets_tree_sha256': tree}, sort_keys=True), flush=True)
    return record


def main():
    materialize('uncapped-B-recipe-roomfix', {
        'mix': PILOT / 'mix_v25_uncapped_gtm2_r050_roomfix_20260923',
        'compact': PILOT / 'diagnostic_set_compact_v25_uncapped_20260923',
        'out': PILOT / 'mix_v25_uncapped_gtm2_r050_roomfix_20260923_trainer'})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
