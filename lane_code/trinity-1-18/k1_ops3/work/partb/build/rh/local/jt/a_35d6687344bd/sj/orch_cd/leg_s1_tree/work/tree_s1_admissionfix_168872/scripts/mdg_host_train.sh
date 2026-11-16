#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 3 || ! $2 =~ ^[1-9][0-9]*$ ]]; then
    echo 'Usage: mdg_host_train.sh <config.json> <nproc> <run_dir>' >&2
    exit 2
fi
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source "$repo/scripts/mdg_env.sh"
cd "$repo"
checkout_status=$(git status --porcelain --untracked-files=all)
if [[ -n $checkout_status ]]; then
    echo 'MDG launch requires a clean checkout.' >&2
    exit 1
fi
mkdir -p -- "$3"
exec 9>"$3/.mdg_launch.lock"
flock -n 9 || { echo 'Another launcher holds this run directory.' >&2; exit 1; }
"$MDG_PYTHON" - "$1" "$2" "$3" "$repo" <<'PY'
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import sys

config, nproc, run, repo = Path(sys.argv[1]).resolve(), int(sys.argv[2]), Path(sys.argv[3]).resolve(), Path(sys.argv[4])
git = repo / '.git'
if git.is_file():
    git = (repo / git.read_text().strip().removeprefix('gitdir: ')).resolve()
head = (git / 'HEAD').read_text().strip()
if head.startswith('ref: '):
    ref = head[5:]
    common = (git / (git / 'commondir').read_text().strip()).resolve() if (git / 'commondir').is_file() else git
    if (common / ref).is_file():
        head = (common / ref).read_text().strip()
    else:
        head = next(line.split()[0] for line in (common / 'packed-refs').read_text().splitlines()
                    if not line.startswith(('#', '^')) and line.split()[1] == ref)
if len(head) != 40 or any(c not in '0123456789abcdef' for c in head):
    raise ValueError('Cannot authenticate launch commit')
identity = dict(commit=head, config=str(config), config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(), nproc=nproc)
original = run / 'LAUNCH.json'
if original.exists():
    previous = json.loads(original.read_text())
    if any(previous.get(k) != v for k, v in identity.items()):
        raise ValueError('Resume requires the same commit, config and process count')
    index = 1
    while (run / f'LAUNCH_{index}.json').exists():
        index += 1
    receipt = run / f'LAUNCH_{index}.json'
else:
    if (run / 'train.log').exists():
        raise ValueError('Unreceipted existing train.log must be preserved')
    receipt = original
with receipt.open('x') as stream:
    json.dump(dict(schema='mdg-host-launch-v1', **identity, hostname=socket.gethostname(),
                   utc=datetime.now(timezone.utc).isoformat()), stream, sort_keys=True)
    stream.write('\n')
PY
exec torchrun --standalone --nproc_per_node "$2" -m student_pilot.mdg_train train --config "$1" >>"$3/train.log" 2>&1
