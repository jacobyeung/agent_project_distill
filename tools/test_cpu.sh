#!/bin/bash
# tools/test_cpu.sh [pytest args, e.g. test paths]: run pytest on CPU with /home and /data* hidden.
# The repository and a temporary directory are the only writable paths; HOME=/tmp is an empty tmpfs.
# Paths listed under cpu_skip in tools/pytest_cpu.ini are not collected and are printed with their reason.
# CPU_PYTHON picks the interpreter (default p1cpu); CPU_TEST_TMP the temporary directory (default <repo>/.tmp/cpu_tests).
set -u
REPO=$(cd "$(dirname "$0")/.." && pwd)
PY=${CPU_PYTHON:-/scratch/jjyeung/envs/p1cpu/bin/python}
TMP=${CPU_TEST_TMP:-$REPO/.tmp/cpu_tests}
mkdir -p "$TMP"
TMP=$(cd "$TMP" && pwd)
[ $# -gt 0 ] || set -- tools/orchkit/tests tools/tests
cd "$REPO" || exit 2
exec bwrap --ro-bind / / \
  --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /tmp \
  --bind "$REPO" "$REPO" --bind "$TMP" "$TMP" --dev /dev --proc /proc --chdir "$REPO" \
  --setenv HOME /tmp --setenv TMPDIR "$TMP" --setenv PYTHONDONTWRITEBYTECODE 1 \
  --setenv PYTHONPATH "$REPO/tools" \
  "$PY" -s -m pytest -q -p no:cacheprovider -c tools/pytest_cpu.ini --rootdir "$REPO" -p pytest_cpu_plugin "$@"
