#!/usr/bin/env bash
set -euo pipefail
root="$(dirname -- "$(dirname -- "$(realpath -- "${BASH_SOURCE[0]}")")")"
exec "$root/work/launch.sh" pi3x_g3t_clip_scale "$@"
