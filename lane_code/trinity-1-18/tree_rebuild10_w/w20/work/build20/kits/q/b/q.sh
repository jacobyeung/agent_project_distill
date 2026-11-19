#!/bin/bash
set -eu
ROOT="$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")"
exec /bin/bash "$ROOT/job.sh" "$@"
