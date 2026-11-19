#!/bin/bash
set -euo pipefail
umask 077
D=$(cd -- "$(dirname -- "$0")" && pwd)
P=/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/ed73cebe51dc4d8a9f3bf4d27610f4d7/package
if [ "${1:-}" != --worker ]; then
  mkdir -m 700 "$P/a/0.lock"
  test ! -e "$P/a/1.txt"
  nohup bash "$0" --worker </dev/null >"$P/a/0.log" 2>&1 &
  printf '%s\n' "$!" > "$P/a/0.txt"
  exit 0
fi
test -d "$P/a/0.lock"
fin(){ rc=$?; printf '%s\n' "$rc" > "$P/a/1.txt"; exit "$rc"; }
trap fin EXIT
sleep 0.15
exit 0
