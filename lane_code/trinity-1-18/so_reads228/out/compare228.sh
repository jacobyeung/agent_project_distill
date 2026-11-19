#!/usr/bin/env bash
set -euo pipefail
date -u
kit_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$kit_dir/control_environment228.sh"
control_python="${READ228_CONTROL_PYTHON:-/scratch/jjyeung/orch_n30/reads228/private_rt/sj/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12}"
exec nice -n 10 "$control_python" -B -I "$kit_dir/compare228.py" "$@"
