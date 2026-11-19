#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/okh7/a15_cot_apd60a20ec01296
cd "$P"
JOB=$(cat "$P/a/8.txt")
[[ "$JOB" =~ ^[0-9]+$ ]]
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PYCODE'
import sys
print('d60a20ec01296'+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B "$P/a/7.py" --package "$P" --return-token "$RET" --out "$P/a/f"
ls -la $P/a/f; cat $P/a/f/EXIT.json | head -c 600; echo; ls -la /project/community/jjyeung/okh7/ae71c903 | tail -5; for d in /project/community/jjyeung/okh7/ae71c903/*/; do du -sb $d; done | tail -5; TZ=UTC squeue -u jjyeung -h -o "%i %j %P %T %M"
