"""Validate the camera-only step-600 return before using the unchanged scorer."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPORT_FIELDS = ('archive_sha256', 'archive_bytes', 'object', 'member_directory', 'step')


def read(path):
    return json.loads(Path(path).read_text())


def require(actual, expected, label):
    if type(actual) is not type(expected) or actual != expected:
        raise ValueError(label + ' differs from READ_PLAN_C600.json')


def validate(root, package, plan_path):
    root, package = Path(root), Path(package)
    plan = read(plan_path)
    binding = plan['export_binding']
    require(binding['step'], 600, 'Plan step')
    pin = read(root / 'metadata/EXPORT_PIN.json')
    if 'archive_bytes' not in pin:
        # cont_ops22: real returns omit archive_bytes; take it from the authenticated INPUTS part list.
        archives = read(root / 'metadata/INPUTS.json')['archives']
        pin['archive_bytes'] = sum(part['bytes'] for part in archives[0]['parts'])
    for key in EXPORT_FIELDS:
        require(pin.get(key), binding[key], 'Export ' + key)
    require(read(package / 'READ_PLAN.json'), plan, 'Package read plan')
    public = read(package / 'package/0.json')
    for key in ('token', 'plan_sha256'):
        require(public.get(key), plan[key], 'Package ' + key)
    operator = hashlib.sha256((package / 'tower_sequence.py').read_bytes()).hexdigest()
    require(operator, plan['operator_sha256'], 'Package operator')
    identity = read(root / 'metadata/IDENTITY.json')
    for key, plan_key in (('plan', 'plan_sha256'), ('operator_sha256', 'operator_sha256'),
                          ('reads', 'read_settings'), ('schedule', 'sequence')):
        require(identity.get(key), plan[plan_key], 'Return ' + key)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--read-plan', type=Path, default=HERE / 'READ_PLAN_C600.json')
    parser.add_argument('--package-root', type=Path, required=True,
                        help='Scorer A directory containing READ_PLAN.json, package and src')
    parser.add_argument('--step', type=int, choices=(600,), default=600)
    parser.add_argument('--a', required=True)
    parser.add_argument('--baseline-root', type=Path)
    parser.add_argument('--out', required=True)
    parser.add_argument('--b', help=argparse.SUPPRESS)
    parser.add_argument('--self-test', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.b or args.self_test:
        parser.error('This wrapper requires a camera-only A return')
    package = args.package_root.resolve()
    if package.name != 'A':
        parser.error('--package-root must identify the scorer A directory')
    try:
        validate(args.a, package, args.read_plan)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.error(str(error))
    spec = importlib.util.spec_from_file_location('score_r5_look_c600', HERE / 'in/out4s/score_r5_look.py')
    scorer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scorer)
    scorer.O = package.parent
    previous = sys.argv
    try:
        sys.argv = [str(spec.origin), '--step', '600', '--a', args.a, '--out', args.out]
        if args.baseline_root is not None:
            sys.argv += ['--baseline-root', str(args.baseline_root)]
        scorer.main()
    finally:
        sys.argv = previous


if __name__ == '__main__':
    main()
