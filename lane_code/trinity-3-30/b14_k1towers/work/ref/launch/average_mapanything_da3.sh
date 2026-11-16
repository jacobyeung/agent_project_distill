#!/usr/bin/env bash
set -euo pipefail
root="$(dirname -- "$(dirname -- "$(realpath -- "${BASH_SOURCE[0]}")")")"
exec "$root/work/launch.sh" average_mapanything_da3 "$@"
