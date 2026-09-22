import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .assets import load_scene
from .blocking import benchmark_blocking, overlap
from .generate import counts
from .io import canonical, digest, pin, read_json, read_jsonl, verify_pin
from .mix import measurement_rows
from .questions import generate_scene
from .split import load_split
from .targets import render_target


def verify_dataset(directory, recompute=False):
    directory = Path(directory).resolve()
    sides, manifest, split_record, _ = measurement_rows(directory)
    config = manifest['config']
    conventions = read_json(directory / 'CONVENTIONS.json')
    if digest(conventions) != config['conventions_sha256']:
        raise ValueError('conventions differ from the generation config')
    verify_pin(manifest['inputs']['split'])
    policy = load_split(manifest['inputs']['split']['path'])
    if policy.record(sides['train'], sides['heldout']) != split_record:
        raise ValueError('split record does not replay the published scene partition')
    all_rows = sorted([*sides['train'], *sides['heldout']], key=lambda row: row['qid'])
    if counts(all_rows) != manifest['counts']['all']:
        raise ValueError('complete row census differs from manifest')
    evaluation, _ = benchmark_blocking(manifest['benchmark_blocking'])
    overlap_census = overlap([{'dataset': row['dataset'], 'scene_name': row['scene']} for row in all_rows], evaluation)
    if overlap_census != manifest['overlap'] or overlap_census['any']:
        raise ValueError('benchmark blocking does not replay')
    by_scene = defaultdict(list)
    for row in all_rows:
        if render_target(row['observations'], row['ground_truth']['answer'], row['derivations']) != row['target']:
            raise ValueError('target bytes differ from their measurement lines')
        by_scene[row['dataset'], row['scene']].append(row)
    coverage = read_json(directory / 'COVERAGE.json')
    entries = coverage['scenes']
    if len(entries) != coverage['prepared_scenes'] or len({(e['dataset'], e['scene_name']) for e in entries}) != len(entries):
        raise ValueError('coverage denominator does not reconcile')
    if dict(Counter(entry['status'] for entry in entries)) != coverage['by_status']:
        raise ValueError('coverage status census mismatch')
    requested = [entry for entry in entries if entry['status'] != 'not_requested']
    if len(requested) != coverage['selected_scenes']:
        raise ValueError('selected-scene denominator does not reconcile')
    if set(by_scene) != {(entry['dataset'], entry['scene_name']) for entry in entries if entry['rows']}:
        raise ValueError('row-bearing scenes differ from coverage')
    replayed = 0
    for entry in requested:
        key = entry['dataset'], entry['scene_name']
        for spec in entry['checkpoint'].values():
            verify_pin(spec)
        checkpoint_rows = list(read_jsonl(entry['checkpoint']['rows']['path']))
        checkpoint_coverage = read_json(entry['checkpoint']['coverage']['path'])
        if checkpoint_coverage != {key: value for key, value in entry.items() if key != 'checkpoint'}:
            raise ValueError('scene checkpoint coverage differs from final coverage')
        rows = by_scene.get(key, [])
        if checkpoint_rows != rows or len(rows) != entry['rows']:
            raise ValueError('scene checkpoint rows differ from final row files')
        if entry['status'] == 'generated':
            verify_pin(entry['receipt'])
            if recompute:
                scene = load_scene(entry['receipt']['path'])
                replay, _ = generate_scene(scene, conventions, seed=config['seed'], density=config['density'],
                                            config_sha=manifest['config_sha256'], commit=manifest['repo_commit'])
                if canonical(replay) != canonical(rows):
                    raise ValueError('scene geometry replay changed generated row bytes')
                replayed += 1
    summary = {'verdict': 'COMPLETE', 'checked_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
               'manifest': pin(directory / 'MANIFEST.json'), 'counts': manifest['counts'],
               'prepared_scenes': coverage['prepared_scenes'], 'selected_scenes': coverage['selected_scenes'],
               'generated_scenes': coverage['by_status'].get('generated', 0), 'replayed_scenes': replayed,
               'deferred_scenes': sum(entry['status'].startswith('deferred') for entry in requested),
               'benchmark_overlap': overlap_census['any'], 'heldout_in_train': split_record['counts']['heldout_in_train']}
    return summary, all_rows, coverage


def sample_text(directory, summary, rows, coverage):
    lines = ['# Ground-truth measurement sample', '',
             f'This sample contains {len(rows)} rendered targets from {summary["generated_scenes"]} authenticated training scenes.',
             f'Generator output: `{Path(directory).resolve()}`.',
             'Every target below is copied verbatim from the row files. The Markdown fence separator is not part of the target.',
             'Floor-area labels measure the annotated mesh footprint; missing floor geometry does not certify the complete physical room area.', '']
    sides = {}
    for side in ('train', 'heldout'):
        for row in read_jsonl(Path(directory) / (side + '.jsonl')):
            sides[row['qid']] = side
    by_scene = defaultdict(list)
    for row in rows:
        by_scene[row['dataset'], row['scene']].append(row)
    for entry in coverage['scenes']:
        key = entry['dataset'], entry['scene_name']
        if key not in by_scene:
            continue
        lines += [f'## {key[0]}/{key[1]}', '', 'These pinned assets supply every measurement in this scene.', '']
        for name, spec in {'scene_receipt': entry['receipt'], **entry['assets']}.items():
            lines.append(f'- {name}: `{spec["path"]}`; SHA-256 `{spec["sha256"]}`.')
        lines += ['', 'The scene receipt and each row pin all 32 RGB frames separately.', '']
        for row in by_scene[key]:
            lines += [f'### {row["qid"]}', '', f'Family: `{row["family"]}`. Split: `{sides[row["qid"]]}`. Frame: `{row["frame_index"]}`. Objects: `{canonical(row["object_ids"])}`.',
                      '', 'Ground truth: `' + canonical(row['ground_truth']) + '`.', '',
                      f'Wording authority: `{row["provenance"]["template"]["authority"]["path"]}`, line {row["provenance"]["template"]["line"]}.',
                      '', 'Question:', '```text', row['student_input']['question'], '```', '', 'Rendered target:', '```text', row['target'], '```', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Authenticate coverage and rows, optionally replay geometry, and render the requested human-review sample.')
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--recompute', action='store_true')
    parser.add_argument('--expect-scenes', type=int)
    parser.add_argument('--sample', type=Path, help='Explicit, new human-review artifact path; its parent must already exist.')
    args = parser.parse_args()
    summary, rows, coverage = verify_dataset(args.directory, args.recompute)
    if args.expect_scenes is not None and summary['generated_scenes'] != args.expect_scenes:
        raise ValueError('generated-scene census differs from the requested sample')
    if args.sample:
        with args.sample.open('x') as handle:
            handle.write(sample_text(args.directory, summary, rows, coverage))
    print(canonical(summary))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
