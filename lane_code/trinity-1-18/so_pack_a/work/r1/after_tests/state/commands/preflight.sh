#!/bin/bash
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\n" "$rc" "$LINENO" >&2; fi' EXIT
/usr/bin/python3 -I -s -B - <<'PYCODE'
from pathlib import Path
pins={'/project/community/jjyeung/okh7/eabcdef012345/1': 20480, '/project/community/jjyeung/okh7/eabcdef012345/2': 10240, '/project/community/jjyeung/okh7/eabcdef012345/3': 10240, '/project/community/jjyeung/okh7/eabcdef012345/4': 10240, '/project/community/jjyeung/okh7/eabcdef012345/0': 14, '/project/community/jjyeung/okh7/eabcdef012345/5': 2560, '/project/community/jjyeung/okh7/eabcdef012345/6': 2560, '/project/community/jjyeung/okh7/eabcdef012345/7': 2560, '/project/community/jjyeung/okh7/eabcdef012345/8': 2560, '/project/community/jjyeung/okh7/eabcdef012345/9': 101, '/project/community/jjyeung/okh7/eabcdef012345/10': 243, '/project/community/jjyeung/okh7/eabcdef012345/11': 121, '/project/community/jjyeung/okh7/eabcdef012345/12': 401}
for name,size in pins.items():
 p=Path(name)
 if not p.is_file() or p.stat().st_size!=size:raise ValueError('Required staged input missing or size differs: '+name)
print('inputs ready')
PYCODE
