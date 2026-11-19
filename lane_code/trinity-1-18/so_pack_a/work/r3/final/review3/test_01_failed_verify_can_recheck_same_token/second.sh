#!/bin/bash
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\n" "$rc" "$LINENO" >&2; fi' EXIT
/usr/bin/python3 -I -s -B - <<'PYCODE'
import os
from pathlib import Path
p=Path('/scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/review3/test_01_failed_verify_can_recheck_same_token/retry')
p.mkdir(mode=0o700,exist_ok=True)
assert not p.is_symlink() and p.stat().st_uid==os.getuid() and not p.stat().st_mode & 0o077
assert {x.name for x in p.iterdir()}<={'v'}, 'Verify cannot run after placement'
v=p/'v'
try:v.mkdir(mode=0o700)
except FileExistsError:
 assert not v.is_symlink() and v.is_dir() and not v.stat().st_mode & 0o077
 failed=v/'0.exit'
 assert failed.is_file() and not failed.is_symlink() and failed.stat().st_size<16 and not (v/'0.txt').exists(), 'Verification active, successful or uncertain; do not relaunch'
 assert 0<int(failed.read_text())<256, 'Invalid verification failure receipt'
 archive=v/os.urandom(8).hex();archive.mkdir(mode=0o700)
 failed.rename(archive/'0.exit')
 for name in ('0.sh','0.log','0.json'):
  old=v/name
  if old.exists():
   assert not old.is_symlink() and old.is_file()
   old.rename(archive/name)
(v/'0.sh').write_text('#!/bin/bash\numask 077\nsleep 1\nprintf "0\\n" >v/0.txt\n')

PYCODE
cd /scratch/jjyeung/orch_n30/so_pack_a/work/r3/final/review3/test_01_failed_verify_can_recheck_same_token/retry
setsid nohup bash v/0.sh </dev/null >v/0.log 2>&1 &
