#!/usr/bin/env bash
set -euo pipefail
root="$(dirname -- "$(dirname -- "$(realpath -- "${BASH_SOURCE[0]}")")")"
exec "$root/work/launch.sh" moge3_g3t_frame_affine "$@"
