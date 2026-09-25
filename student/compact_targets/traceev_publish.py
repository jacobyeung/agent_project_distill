"""Re-publish trace-evidence rows from the authenticated per-scene shards of a finished extraction run.

The extraction run's global per-scene cap (1/200 of the published rows) assumed thousands of scenes; the v3 train side has 276 scene
frame sets, so that cap kept 5,235 of 16,316 admissible facts. This step re-applies dedupe_rows and select_budget (all other caps
unchanged) with a configurable per-scene share, without re-running the extraction. Shard rows are byte-identical inputs; the only
field select_budget adds is evidence.owner_qid, exactly as in extract().
"""
import argparse
import json
import os
from collections import Counter
from pathlib import Path

from . import traceev_extract as X


def publish(args):
    require = X.require
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_environment_required')
    source = args.from_run
    inputs = X.read_json(source / 'BUILD_INPUTS.json')
    source_summary = X.read_json(source / 'SUMMARY.json')
    rows, stats, shards = [], {}, []
    for done in sorted((source / 'shards').glob('*.done.json')):
        record = X.read_json(done)
        require(X.sha(record['path']) == record['sha256'], 'scene_shard_digest_mismatch')
        with Path(record['path']).open() as stream:
            rows.extend(json.loads(line) for line in stream)
        X.aggregate_stats(stats, record['stats'])
        shards.append({'path': record['path'], 'sha256': record['sha256']})
    require(len(shards) == source_summary['scene_shards'], 'shard_count_mismatch')
    commit = X.source_commit()
    args.out.mkdir(parents=True, exist_ok=False)
    candidates, dedupe_drops = X.dedupe_rows(rows)
    selected, budget_drops = X.select_budget(candidates, args.budget, args.seed, args.scene_share)
    selected.sort(key=lambda row: (row['dataset'], row['scene'], row['qid']))
    path = args.out / 'evidence_rows.jsonl'
    with path.open('x') as stream:
        for row in selected:
            stream.write(X.canonical(row) + '\n')
    source_drops = Counter(X.read_json(source / 'DROPS.json')['counts'])
    for key in list(source_drops):
        if key.startswith('budget_') or key in ('duplicate_fact', 'dedupe_conflicting_render'):
            del source_drops[key]
    drops = source_drops + dedupe_drops + budget_drops
    X.write_json(args.out / 'DROPS.json', {'counts': drops, 'source_run': str(source)})
    owners = Counter(row['evidence']['owner_qid'] for row in selected)
    scenes = Counter(row['dataset'] + '/' + row['scene'] for row in selected)
    publish_inputs = {'source_run': str(source), 'source_build_inputs_sha256': X.sha(source / 'BUILD_INPUTS.json'),
                      'source_summary_sha256': X.sha(source / 'SUMMARY.json'), 'source_extractor_commit': source_summary['commit'],
                      'source_config_sha256': source_summary['config_sha256'], 'shards': shards, 'publish_commit': commit,
                      'budget': args.budget, 'seed': args.seed, 'scene_share': args.scene_share, 'started_utc': X.utc()}
    X.write_json(args.out / 'PUBLISH_INPUTS.json', publish_inputs)
    summary = {'path': str(path), 'sha256': X.sha(path), 'rows': len(selected), 'commit': source_summary['commit'],
               'publish_commit': commit, 'config_sha256': source_summary['config_sha256'], 'scene_share': args.scene_share,
               'max_scene_rows': max(scenes.values()) if scenes else 0, 'scenes': len(scenes),
               'per_kind': {kind: sum(row['question_type'] == kind for row in selected) for kind in X.KINDS},
               'per_supported_type': dict(Counter(support for row in selected for support in row['supports'])),
               'raw_per_kind': dict(Counter(row['question_type'] for row in candidates)),
               'source_question_types': stats.get('trace_types', {}), 'eligible_traces': inputs['eligible_traces'],
               'traces_processed': stats.get('traces_processed', 0), 'facts_per_trace': stats.get('facts_per_trace', {}),
               'new_facts_per_trace': dict(Counter(map(str, owners.values()))),
               'candidate_scenes': len({(row['dataset'], row['scene']) for row in candidates}),
               'frame_mapping_passed': stats.get('frame_mapping_passed', 0), 'frame_pairs_checked': stats.get('frame_pairs_checked', 0),
               'count_distribution': dict(Counter(str(X.count_value(row)) for row in selected if row['question_type'] == 'traceev_count_list')),
               'raw_count_distribution': dict(Counter(str(X.count_value(row)) for row in candidates if row['question_type'] == 'traceev_count_list')),
               'label_checks': X.label_check_summary(selected), 'raw_label_checks': X.label_check_summary(candidates),
               'agreements': {name: X.distribution(values) for name, values in stats.get('agreements', {}).items()},
               'drops': drops, 'workers': inputs.get('workers'), 'scene_shards': len(shards),
               'tool_names': stats.get('tool_names', {}), 'frame_modes': stats.get('frame_modes', {}), 'finished_utc': X.utc()}
    X.composition(args.out, summary, selected, candidates)
    X.write_json(args.out / 'SUMMARY.json', summary)
    print(X.canonical({k: summary[k] for k in ('path', 'sha256', 'rows', 'per_kind', 'max_scene_rows', 'scenes')}), flush=True)
    return summary


def parser():
    root = argparse.ArgumentParser()
    root.add_argument('--from-run', type=Path, required=True)
    root.add_argument('--out', type=Path, required=True)
    root.add_argument('--budget', type=int, default=40000)
    root.add_argument('--seed', type=int, default=20260925)
    root.add_argument('--scene-share', type=int, default=50, help='per-scene cap = published rows // scene_share (50 -> 2 percent)')
    return root


if __name__ == '__main__':
    publish(parser().parse_args())
