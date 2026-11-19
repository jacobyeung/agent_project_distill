#!/bin/bash
export PYTHONDONTWRITEBYTECODE=1
set -eu
ROOT="$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")"
exec /bin/bash "$ROOT/job.sh" "$@"
