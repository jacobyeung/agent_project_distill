import argparse
import json
import sys
from pathlib import Path


def main(argv=None):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('student_pilot/orchard_eval/__main__.py:main')
    parser = argparse.ArgumentParser(description='Matched RGB-only local student benchmark evaluation')
    sub = parser.add_subparsers(dest='command', required=True)
    repo = Path(__file__).resolve().parents[2]

    def output_args(command):
        command.add_argument('--output', required=True)
        command.add_argument('--artifact-root', default=str(repo / 'artifacts/paper_eval'))

    prepare = sub.add_parser('prepare')
    prepare.add_argument('--benchmark', choices=('vsibench_answerable500', 'vstibench_repr450_v2', 'dsibench_all4'), required=True)
    prepare.add_argument('--config', required=True)
    prepare.add_argument('--data-root', required=True)
    prepare.add_argument('--media-root')
    prepare.add_argument('--membership')
    prepare.add_argument('--provenance')
    prepare.add_argument('--project-root')
    prepare.add_argument('--dataset-manifest')
    prepare.add_argument('--media-index')
    prepare.add_argument('--synthetic', action='store_true')
    output_args(prepare)
    check = sub.add_parser('cpu-check')
    check.add_argument('--manifest', required=True)
    check.add_argument('--model', choices=('onethinker', 'qwen35', 'qwen36_27b'), required=True)
    check.add_argument('--model-root')
    check.add_argument('--synthetic', action='store_true')
    check.add_argument('--variant', choices=('base', 'distilled'), default='base')
    check.add_argument('--adapter')
    check.add_argument('--training-receipt')
    check.add_argument('--checkpoint-dir')
    output_args(check)
    smoke = sub.add_parser('cpu-smoke')
    smoke.add_argument('--config', required=True)
    smoke.add_argument('--fixtures-root', default=str(repo / 'tests/fixtures/benchmark_eval'))
    smoke.add_argument('--project-root', required=True)
    smoke.add_argument('--official-python', default=sys.executable)
    output_args(smoke)
    generate = sub.add_parser('generate')
    generate.add_argument('--manifest', required=True)
    generate.add_argument('--model', choices=('onethinker', 'qwen35', 'qwen36_27b'), required=True)
    generate.add_argument('--variant', choices=('base', 'distilled'), required=True)
    generate.add_argument('--preflight', required=True)
    generate.add_argument('--model-root')
    generate.add_argument('--lease')
    generate.add_argument('--coord-root')
    generate.add_argument('--adapter')
    generate.add_argument('--training-receipt')
    generate.add_argument('--checkpoint-dir')
    generate.add_argument('--device-mode', choices=('single', 'sharded'), default='single')
    generate.add_argument('--base-run')
    generate.add_argument('--allow-unpaired-adapter', action='store_true',
                          help='Evaluate a labeled adapter for an external parent comparison without a cold-base run')
    generate.add_argument('--resume', action='store_true')
    generate.add_argument('--cpu-mock', action='store_true')
    generate.add_argument('--shard-index', type=int, default=0, help='Zero-based manifest-order shard index')
    generate.add_argument('--shard-count', type=int, default=1, help='Number of manifest-order shards')
    generate.add_argument('--shard-manifest', help='Assignment manifest output; defaults to OUTPUT/shards/I.manifest.json for multiple shards')
    output_args(generate)
    score = sub.add_parser('score')
    score.add_argument('--run', required=True)
    score.add_argument('--scoring-manifest', required=True)
    score.add_argument('--official-python', default=sys.executable)
    output_args(score)
    compare = sub.add_parser('compare')
    compare.add_argument('--base', required=True)
    compare.add_argument('--distilled', required=True)
    output_args(compare)
    export = sub.add_parser('export-bank')
    export.add_argument('--run', required=True)
    export.add_argument('--score', required=True)
    export.add_argument('--bank-id', required=True)
    output_args(export)
    for command in (check, generate):
        command.add_argument('--thinking', choices=('pinned', 'off'), default='pinned')
        command.add_argument('--max-new-tokens', type=int, default=4096,
                             help='Positive output budget; larger-budget paper controls require --items-file')
        command.add_argument('--items-file', help='Non-empty JSON array of unique qid strings in manifest order; a proper subset')
        command.add_argument('--allow-distilled-controls', action='store_true',
                             help='Explicitly allow non-default controls on a matched distilled arm')
    for command in (check, generate):
        command.add_argument('--geometry-store-manifest',
                             help='Eval feature store manifest of a geometry-input publication (with --geometry-store-sha256)')
        command.add_argument('--geometry-store-sha256', help='sha256 of --geometry-store-manifest')
        command.add_argument('--geometry-camera-manifest',
                             help='Eval camera sidecar manifest of a G3T-prior geometry store (with --geometry-camera-sha256)')
        command.add_argument('--geometry-camera-sha256', help='sha256 of --geometry-camera-manifest')
        command.add_argument('--carriers', choices=('none', 'insert'),
                             help='Camera carriers; required for a publication with a camera head (insert: the trained '
                                  'c_first/c_rest tokens after each temporal group, as in training)')
        command.add_argument('--headcall', choices=('none', 'decode'),
                             help='decode: the trace calls the published heads mid-generation and the loop inserts '
                                  'their answers (needs --carriers insert and a full-weights publication)')
    from .contracts import PROVISIONAL_LABELS as LABELS
    for command in (check, generate, score, compare):
        command.add_argument('--provisional-diagnostic', choices=LABELS)
    args = parser.parse_args(argv)
    # A cell named *_vstiv3 reads VSTI-450 v3's prepared manifests (the code-aws evaluator patch). --carriers keeps no
    # default: a camera-head publication refuses unless the option is explicit.
    out_cell = Path(getattr(args, 'output', None) or '').resolve().parent.name
    if out_cell.endswith('_vstiv3'):
        if getattr(args, 'manifest', None):
            args.manifest = str(args.manifest).replace('/vstibench_repr450_v2/', '/vstibench_repr450_v3/')
        if getattr(args, 'scoring_manifest', None):
            args.scoring_manifest = str(args.scoring_manifest).replace('/vstibench_repr450_v2/', '/vstibench_repr450_v3/')
    geometry_store = None
    if args.command in ('cpu-check', 'generate') and (args.geometry_store_manifest, args.geometry_store_sha256) != (None, None):
        if None in (args.geometry_store_manifest, args.geometry_store_sha256):
            parser.error('--geometry-store-manifest and --geometry-store-sha256 are given together')
        geometry_store = {'manifest': args.geometry_store_manifest, 'manifest_sha256': args.geometry_store_sha256}
    if args.command in ('cpu-check', 'generate') and (args.geometry_camera_manifest, args.geometry_camera_sha256) != (None, None):
        if None in (args.geometry_camera_manifest, args.geometry_camera_sha256) or geometry_store is None:
            parser.error('--geometry-camera-manifest and --geometry-camera-sha256 are given together with --geometry-store-manifest')
        geometry_store['camera_manifest'] = args.geometry_camera_manifest
        geometry_store['camera_manifest_sha256'] = args.geometry_camera_sha256
    if args.command == 'prepare':
        from .prepare import prepare as run
        result = run(args.benchmark, args.config, args.output, args.artifact_root, args.data_root,
                     args.media_root, args.membership, args.provenance, args.project_root,
                     args.dataset_manifest, args.media_index, args.synthetic)
    elif args.command == 'cpu-check':
        from .frames import cpu_check
        result = cpu_check(args.manifest, args.model, args.output, args.artifact_root, args.model_root,
                           args.synthetic, args.variant, args.adapter, args.training_receipt,
                           provisional_diagnostic=args.provisional_diagnostic, thinking=args.thinking,
                           max_new_tokens=args.max_new_tokens, items_file=args.items_file,
                           allow_distilled_controls=args.allow_distilled_controls, checkpoint_dir=args.checkpoint_dir,
                           geometry_store=geometry_store, carriers=args.carriers,
                           **({'headcall': args.headcall} if args.headcall is not None else {}))
    elif args.command == 'cpu-smoke':
        from .prepare import cpu_smoke
        result = cpu_smoke(args.config, args.output, args.artifact_root, args.fixtures_root,
                           args.project_root, args.official_python)
    elif args.command == 'generate':
        from .generate import generate_run
        result = generate_run(args.manifest, args.model, args.variant, args.output, args.artifact_root,
                              args.preflight, args.lease, args.coord_root, args.model_root,
                              args.adapter, args.training_receipt, args.resume, args.cpu_mock, paired_base_run=args.base_run,
                              provisional_diagnostic=args.provisional_diagnostic,
                              shard_index=args.shard_index, shard_count=args.shard_count, shard_manifest=args.shard_manifest,
                              thinking=args.thinking, max_new_tokens=args.max_new_tokens, items_file=args.items_file,
                              allow_distilled_controls=args.allow_distilled_controls, device_mode=args.device_mode,
                              checkpoint_dir=args.checkpoint_dir, geometry_store=geometry_store, carriers=args.carriers,
                              **({'allow_unpaired_adapter': True} if args.allow_unpaired_adapter else {}),
                              **({'headcall': args.headcall} if args.headcall is not None else {}))
    elif args.command == 'score':
        from .score import score_run
        result = score_run(args.run, args.scoring_manifest, args.output, args.artifact_root, args.official_python,
                           provisional_diagnostic=args.provisional_diagnostic)
    elif args.command == 'compare':
        from .score import compare_scores
        result = compare_scores(args.base, args.distilled, args.output, args.artifact_root,
                                provisional_diagnostic=args.provisional_diagnostic)
    else:
        from .score import export_bank
        result = export_bank(args.run, args.score, args.bank_id, args.output, args.artifact_root)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
