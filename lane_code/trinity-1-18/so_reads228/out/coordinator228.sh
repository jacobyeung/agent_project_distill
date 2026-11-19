#!/usr/bin/env bash
# Run once in an existing target-node session after the governed staging streams finish.
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo 'Usage: bash coordinator228.sh <card-index-or-UUID> <fresh-local-run-directory>' >&2
  exit 2
fi
date -u
if [[ "$(hostname -s)" != trinity-2-28 ]]; then
  echo 'REFUSED: coordinator228.sh is restricted to trinity-2-28' >&2
  exit 2
fi
kit_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$kit_dir" != /scratch/jjyeung/orch_n30/reads228/kit ]]; then
  echo 'REFUSED: kit must be /scratch/jjyeung/orch_n30/reads228/kit because a/6 is pinned there' >&2
  exit 2
fi
source "$kit_dir/control_environment228.sh"
package="$kit_dir/A10b"
stage=/scratch/jjyeung/orch_n30/reads228
# Check all MISSING.json hashes ourselves; marker files alone are insufficient.
nice -n 10 /usr/bin/python3 -I -s -B "$kit_dir/stage228.py" "$package" --verify-runtime-pins
date -u
# Extraction never overwrites existing members. Input tar uses --skip-old-files.
nice -n 10 /usr/bin/python3 -I -s -B "$kit_dir/stage228.py" "$package" --extract-runtime
date -u
nice -n 10 /usr/bin/python3 -I -s -B "$kit_dir/stage228.py" "$package" --extract-inputs
date -u
nice -n 10 /usr/bin/python3 -I -s -B "$kit_dir/stage228.py" "$package" --install-code
date -u
nice -n 10 /usr/bin/python3 -I -s -B "$kit_dir/stage228.py" "$package" --check-namespace
date -u
export READ228_CONTROL_PYTHON=/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12
# Native CPython controls the job; unchanged d/v/py runs prepare and the worker in bwrap.
nice -n 10 "$READ228_CONTROL_PYTHON" -B -I "$kit_dir/stage228.py" "$package" --prepare --out "$stage/STAGE_CHECK.json"
date -u
nice -n 10 "$READ228_CONTROL_PYTHON" -B -I "$kit_dir/stage228.py" "$package" --out "$stage/STAGE_CHECK.json"
date -u
# Stage verification, both >=300-second idle readings and the run share one launcher.
# A busy card exits immediately. Nothing here retries a killed or failed command.
bash "$kit_dir/run228.sh" "$package" "$1" "$2" --items 50
date -u
compare_rc=0
bash "$kit_dir/compare228.sh" "$2/ret" --orchard "$kit_dir/reference" --out "$2/COMPARE.json" || compare_rc=$?
if [[ "$compare_rc" -gt 1 ]]; then exit "$compare_rc"; fi
date -u
run_name="$(basename -- "$2")"
if [[ ! "$run_name" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]]; then
  echo 'REFUSED: unsafe ingest directory name' >&2; exit 2
fi
# The unchanged unpacker requires --out inside the kit (the A10b parent directory).
accepted="$kit_dir/ingest/$run_name"
nice -n 10 "$READ228_CONTROL_PYTHON" -I -s -B "$kit_dir/unpack228.py" --operator "$package" \
  --archive "$2/return/result.tar.gz" --exit "$2/return/EXIT.json" --out "$accepted"
date -u
# A clean 50/636 envelope has EXIT.status=FAILED. Ingest uses SUMMARY instead.
nice -n 10 "$READ228_CONTROL_PYTHON" -I -s -B "$kit_dir/ingest228.py" --return "$accepted" \
  --comparison "$2/COMPARE.json" --out "$2/CORPUS_INGEST.json"
date -u
