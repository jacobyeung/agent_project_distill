#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/okh7/a15_cot_apef918d5a0e0f1
cd "$P"
JOB=$(cat "$P/a/8.txt")
[[ "$JOB" =~ ^[0-9]+$ ]]
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PYCODE'
import sys
print('ef918d5a0e0f1'+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B "$P/a/7.py" --package "$P" --return-token "$RET" --out "$P/a/f"
