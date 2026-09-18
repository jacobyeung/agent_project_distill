"""Preparer-only contract. This schema cannot authorize the inherited collector."""
from __future__ import annotations
import argparse
from pathlib import Path
from audit_package import REQUIRED_FILES
from gt_scene_assets import pin, read_json, sha, verify, write_json

HERE = Path(__file__).resolve().parent
SCHEMA = 'r1313-gt-preparer-scannet-v2'
EXTRA_FILES = {'scannet_sens.py', 'scannet_adapter.py', 'scannet_contract.py',
               'validate_scannet.py', 'test_scannet_adapter.py', 'SCANNET_CONVENTION.md',
               'scannet_checks.py', 'verify_scannet_assets.py'}


def census(root=HERE):
    root = Path(root)
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
              and p != root / 'CONTRACT.json'}
    if actual != set(REQUIRED_FILES) | EXTRA_FILES:
        raise ValueError('preparer package file census drift')
    result = {}
    for name in sorted(actual):
        path = root / name
        if path.is_symlink():
            raise ValueError('package symlinks are forbidden')
        if path.suffix == '.py':
            compile(path.read_text(), str(path), 'exec')
        result[name] = sha(path)
    return result


def verify_contract(path, digest, root=HERE):
    if sha(path) != digest:
        raise ValueError('preparer contract digest drift')
    contract = read_json(path)
    if contract.get('schema') != SCHEMA or contract.get('collector_admission') is not False:
        raise ValueError('wrong preparer-only contract')
    if contract['source_files'] != census(root):
        raise ValueError('preparer closure bytes drift')
    verify(contract['plan'])
    return contract


def authenticated_frames(args):
    contract = verify_contract(args.contract, args.contract_sha256)
    requested = Path(args.frames_receipt).resolve()
    matches = [row for row in read_json(contract['plan']['path'])['scenes']
               if row['dataset'] == 'scannet' and row['scene'] == args.scene]
    if len(matches) != 1:
        raise ValueError('ScanNet scene is not unique in the pinned plan')
    spec = matches[0]['frames_receipt']
    if requested != Path(spec['path']).resolve() or args.frames_receipt_sha256 != spec['sha256']:
        raise ValueError('requested RGB receipt differs from pinned PLAN')
    frames = read_json(verify(spec))
    if frames['dataset'] != 'scannet' or frames['scene_name'] != args.scene:
        raise ValueError('RGB receipt corpus/scene identity mismatch')
    return frames, contract


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = write_json(args.output, {'schema': SCHEMA, 'collector_admission': False,
        'source_root': str(HERE), 'source_files': census(), 'plan': pin(args.plan),
        'paid_api_calls': 0, 'gpu_runs': 0,
        'convention': 'SCANNET_CONVENTION.md'})
    verify_contract(result['path'], result['sha256'])
    import json
    print(json.dumps(result))


if __name__ == '__main__':
    main()
