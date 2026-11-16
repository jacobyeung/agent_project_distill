#!/bin/bash
set -euo pipefail
export TZ=UTC
BUN=/project/community/jjyeung/okh7/i_1be16f28
KH=/project/community/jjyeung/okh7/x_4b3114cf
[[ ! -e "$KH" && ! -e /project/community/jjyeung/okh7/r/766136c1 && ! -e "$BUN/p" ]] || { echo 'target exists' >&2; exit 3; }
cd "$BUN"
sha256sum -c sums.txt
python3 -B r.py prepare
python3 -B r.py stage
