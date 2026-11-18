#!/bin/bash
# Uses already staged b04 inputs; never restores, copies, retries or kills.
set -euo pipefail
[[ $# == 5 ]] || { echo 'Usage: gpu_113.sh CARD|cpu SET own i/n OUT' >&2; exit 2; }
kit=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
exec bwrap --dev-bind / / --bind /dev/shm/jjyeung /scratch/jjyeung/b04shm \
  bash "$kit/h1eval/h10/host_run.sh" "$@"
