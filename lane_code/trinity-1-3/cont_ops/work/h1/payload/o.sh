#!/bin/bash
set -euo pipefail
export TZ=UTC
umask 077
O=/project/community/jjyeung/okh7
private_dir() {
    [[ -d "$1" && ! -L "$1" && "$(stat -c %a -- "$1")" == 700 ]] || {
        printf 'Directory must be mode 0700; run: chmod 700 -- %q\n' "$1" >&2
        exit 3
    }
}
private_dir "$O"
BUN=/project/community/jjyeung/okh7/i_1be16f28
KH=/project/community/jjyeung/okh7/x_3fdda0fb
private_dir "$BUN"
[[ ! -e "$KH" && ! -e /project/community/jjyeung/okh7/r/39504485 && ! -e "$BUN/p" ]] || { echo 'target exists' >&2; exit 3; }
cd "$BUN"
sha256sum -c sums.txt
python3 -B r.py prepare
python3 -B r.py stage
