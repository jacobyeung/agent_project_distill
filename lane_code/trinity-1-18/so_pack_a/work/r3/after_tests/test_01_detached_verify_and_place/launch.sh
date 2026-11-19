#!/bin/bash
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\n" "$rc" "$LINENO" >&2; fi' EXIT
/usr/bin/python3 -I -s -B - <<'PYCODE'
import os
from pathlib import Path
p=Path('/scratch/jjyeung/orch_n30/so_pack_a/work/r3/after_tests/test_01_detached_verify_and_place/slow')
p.mkdir(mode=0o700,exist_ok=True)
assert not p.is_symlink() and p.stat().st_uid==os.getuid() and not p.stat().st_mode & 0o077
assert not list(p.iterdir()), 'Verify requires an empty token root; do not relaunch'
(p/'v').mkdir(mode=0o700)
(p/'v/0.sh').write_text('#!/bin/bash\nset -eu\numask 077\nsleep 1\nprintf "0\\n" >v/0.txt\n')
PYCODE
cd /scratch/jjyeung/orch_n30/so_pack_a/work/r3/after_tests/test_01_detached_verify_and_place/slow
setsid nohup bash v/0.sh </dev/null >v/0.log 2>&1 &
