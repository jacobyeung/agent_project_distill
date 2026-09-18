import argparse
import json
import sys
from pathlib import Path


def main(argv=None):
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
    check.add_argument('--model', choices=('onethinker', 'qwen35'), required=True)
    check.add_argument('--model-root')
    check.add_argument('--synthetic', action='store_true')
    check.add_argument('--variant', choices=('base', 'distilled'), default='base')
    check.add_argument('--adapter')
    check.add_argument('--training-receipt')
    output_args(check)
    smoke = sub.add_parser('cpu-smoke')
    smoke.add_argument('--config', required=True)
    smoke.add_argument('--fixtures-root', default=str(repo / 'tests/fixtures/benchmark_eval'))
    smoke.add_argument('--project-root', required=True)
    smoke.add_argument('--official-python', default=sys.executable)
    output_args(smoke)
    generate = sub.add_parser('generate')
    generate.add_argument('--manifest', required=True)
    generate.add_argument('--model', choices=('onethinker', 'qwen35'), required=True)
    generate.add_argument('--variant', choices=('base', 'distilled'), required=True)
    generate.add_argument('--preflight', required=True)
    generate.add_argument('--model-root')
    generate.add_argument('--lease')
    generate.add_argument('--coord-root')
    generate.add_argument('--adapter')
    generate.add_argument('--training-receipt')
    generate.add_argument('--base-run')
    generate.add_argument('--resume', action='store_true')
    generate.add_argument('--cpu-mock', action='store_true')
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
    args = parser.parse_args(argv)
    if args.command == 'prepare':
        from .prepare import prepare as run
        result = run(args.benchmark, args.config, args.output, args.artifact_root, args.data_root,
                     args.media_root, args.membership, args.provenance, args.project_root,
                     args.dataset_manifest, args.media_index, args.synthetic)
    elif args.command == 'cpu-check':
        from .frames import cpu_check
        result = cpu_check(args.manifest, args.model, args.output, args.artifact_root, args.model_root,
                           args.synthetic, args.variant, args.adapter, args.training_receipt)
    elif args.command == 'cpu-smoke':
        from .prepare import cpu_smoke
        result = cpu_smoke(args.config, args.output, args.artifact_root, args.fixtures_root,
                           args.project_root, args.official_python)
    elif args.command == 'generate':
        from .generate import generate_run
        result = generate_run(args.manifest, args.model, args.variant, args.output, args.artifact_root,
                              args.preflight, args.lease, args.coord_root, args.model_root,
                              args.adapter, args.training_receipt, args.resume, args.cpu_mock, paired_base_run=args.base_run)
    elif args.command == 'score':
        from .score import score_run
        result = score_run(args.run, args.scoring_manifest, args.output, args.artifact_root, args.official_python)
    elif args.command == 'compare':
        from .score import compare_scores
        result = compare_scores(args.base, args.distilled, args.output, args.artifact_root)
    else:
        from .score import export_bank
        result = export_bank(args.run, args.score, args.bank_id, args.output, args.artifact_root)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
