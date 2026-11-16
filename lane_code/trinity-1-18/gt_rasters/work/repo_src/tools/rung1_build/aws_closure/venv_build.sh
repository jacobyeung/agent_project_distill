#!/usr/bin/env bash
# (rung1_build copy of the awstrain venv_build.sh; the venv path comes from R1_MOUNT.)
# Build the trainer environment once, offline, from the pinned wheel set: the Orchard freeze (60 distributions) with
# torch 2.11.0+cu129 / torchvision 0.26.0+cu129 and their CUDA 12 libraries in place of the CUDA 13 builds, because the
# code-aws driver (575.57, CUDA 12.9) cannot run CUDA 13. Every other distribution and version is Orchard's.
set -euo pipefail
venv="${R1_MOUNT:?}/venvs/rwtrain_torch211_cu129"
wheels=/opt/aws_wheels/cu129/wheels
pins="${ANYHOST_JOBS:?}/pins_cu129.txt"
receipt="$venv.RECEIPT.json"
if [[ -f "$receipt" ]]; then
    cat "$receipt"
    exit 0
fi
mkdir -p "$(dirname "$venv")"
exec 9>>"$venv.lock"
flock 9
if [[ -f "$receipt" ]]; then
    cat "$receipt"
    exit 0
fi
test ! -e "$venv"
/usr/bin/python3 -c 'import sys; assert sys.version_info[:3] == (3, 12, 3), sys.version; print(sys.version)'
/usr/bin/python3 -m venv "$venv"
"$venv/bin/python" -m pip install --no-index --no-deps --find-links "$wheels" -r "$pins"
"$venv/bin/python" -m pip check
"$venv/bin/python" -B - "$pins" "$receipt" <<'PY'
import hashlib
import importlib.metadata as metadata
import json
import sys

pins = {}
for line in open(sys.argv[1]):
    name, _, version = line.strip().partition("==")
    pins[name.lower().replace("_", "-")] = version
installed = {d.metadata["Name"].lower().replace("_", "-"): d.version for d in metadata.distributions()}
missing = {k: v for k, v in pins.items() if installed.get(k) != v}
extra = sorted(set(installed) - set(pins))
assert not missing and not extra, (missing, extra)
import torch
value = {"status": "CU129_ENV_BUILT", "python": sys.version, "executable": sys.executable,
         "pins_sha256": hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest(), "distributions": len(installed),
         "torch": torch.__version__, "torch_cuda": torch.version.cuda}
with open(sys.argv[2], "x") as stream:
    json.dump(value, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(json.dumps(value), flush=True)
PY
