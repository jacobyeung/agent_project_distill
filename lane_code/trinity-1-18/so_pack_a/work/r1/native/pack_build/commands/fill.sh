#!/bin/bash
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\n" "$rc" "$LINENO" >&2; fi' EXIT
/usr/bin/python3 -I -s -B - <<'PYCODE'
from pathlib import Path
p=Path('/project/community/jjyeung/okh7/a15_cot_apb123456789abc')
(p/'a/f.lock').mkdir(mode=0o700)
(p/'a/f.sh').write_text('#!/bin/bash\nset -euo pipefail\numask 077\nexport PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=\ntrap \'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\\n" "$rc" "$LINENO" >&2; fi\' EXIT\ncd /project/community/jjyeung/okh7/a15_cot_apb123456789abc\ntrap \'rc=$?; if [ "$rc" != 0 ]; then printf "%s\\n" "$rc" >a/f.exit; fi\' EXIT\n/usr/bin/python3 -I -s -B /project/community/jjyeung/okh7/a15_cot_apb123456789abc/a/4.py --parts /project/community/jjyeung/okh7/eabcdef012345/5 /project/community/jjyeung/okh7/eabcdef012345/6 /project/community/jjyeung/okh7/eabcdef012345/7 /project/community/jjyeung/okh7/eabcdef012345/8 --done /project/community/jjyeung/okh7/eabcdef012345/9 --object q8/8865619b/673bc60f_m200.tar --config /project/community/jjyeung/okh7/eabcdef012345/10 --receipt /project/community/jjyeung/okh7/eabcdef012345/11 --data-receipt /project/community/jjyeung/okh7/eabcdef012345/12 --lineage SFT --step 200 --out /project/community/jjyeung/okh7/a15_cot_apb123456789abc/a/export.json --prep-tar /project/community/jjyeung/okh7/a15_cot_apb123456789abc/a/6 --base-inputs /project/community/jjyeung/okh7/a15_cot_apb123456789abc/a/0.json --inputs-out /project/community/jjyeung/okh7/a15_cot_apb123456789abc/a/1.json\n/usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:00:00\nprintf "0\\n" > a/1.txt\n')
PYCODE
cd /project/community/jjyeung/okh7/a15_cot_apb123456789abc
setsid nohup bash a/f.sh </dev/null >a/f.log 2>&1 &
