#!/bin/bash
set -euo pipefail
export TZ=UTC
BUN=/project/community/jjyeung/okh7/i_1be16f28
KH=/project/community/jjyeung/okh7/x_4b3114cf
cd "$BUN"
bash z.sh "$@"
