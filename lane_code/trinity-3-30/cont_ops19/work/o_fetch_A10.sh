#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/okh7/a15_cot_apc9399fd2d1158
cd "$P"
JOB=$(cat "$P/a/8.txt")
[[ "$JOB" =~ ^[0-9]+$ ]]
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PYCODE'
import sys
print('c9399fd2d1158'+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B "$P/a/7.py" --package "$P" --return-token "$RET" --out "$P/a/f"
cat $P/a/f/EXIT.json | head -c 700; echo; for f in $P/a/x*; do echo "== $f"; head -3 $f; done
SP=/project/community/jjyeung/okh7/ae71c903; test -d $SP/$RET && ! test -e ${SP}_fetched/$RET && mv $SP/$RET ${SP}_fetched/$RET && echo "moved $RET"; true
