#!/usr/bin/env python
"""Print the repository commit and exact config hash; refuse dirty checkouts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def provenance(config):
    root = Path(__file__).resolve().parents[1]
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env['GIT_OPTIONAL_LOCKS'] = '0'

    def git(*args):
        return subprocess.check_output(
            ['git', '-C', str(root), *args], env=env,
            text=True, stderr=subprocess.PIPE).strip()

    if Path(git('rev-parse', '--show-toplevel')).resolve() != root:
        raise ValueError('the helper must belong to this repository root')
    commit = git('rev-parse', '--verify', 'HEAD')
    digest = hashlib.sha256(Path(config).read_bytes()).hexdigest()
    dirty = bool(git('status', '--porcelain', '--untracked-files=all'))
    return {'repo_commit': commit, 'dirty': dirty, 'config_sha256': digest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    args = parser.parse_args()
    try:
        result = provenance(args.config)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'provenance refused: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    if result['dirty']:
        print('provenance refused: commit changes before launching', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
