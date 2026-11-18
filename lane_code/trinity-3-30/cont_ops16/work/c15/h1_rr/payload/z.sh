#!/bin/bash
set -euo pipefail
export TZ=UTC
BUN=/project/community/jjyeung/okh7/i_1be16f28
KH=/project/community/jjyeung/okh7/x_4b3114cf
cd "$BUN"
case "${1:-}" in
 derive) python3 -B r.py final ;;
 certify) python3 -B r.py certify ;;
 *) echo 'Use derive after independent review; certify after the final content scan.' >&2; exit 2 ;;
esac
