from pathlib import Path
p=Path('/project/community/jjyeung/okh7/a15_cot_apb635a315de01e')
(p/'a/f.lock').mkdir(mode=0o700)
(p/'a/f.sh').write_text('#!/bin/bash\nset -euo pipefail\numask 077\nexport PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=\ntrap \'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\\n" "$rc" "$LINENO" >&2; fi\' EXIT\ncd /project/community/jjyeung/okh7/a15_cot_apb635a315de01e\ntrap \'rc=$?; if [ "$rc" != 0 ]; then printf "%s\\n" "$rc" >a/f.exit; fi\' EXIT\nif then\n/usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 02:30:00\nprintf "0\\n" > a/1.txt\n')
