#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/okh7/a15_cot_apd72cdcff1e22a
cd "$P"
JOB=$(cat "$P/a/8.txt")
[[ "$JOB" =~ ^[0-9]+$ ]]
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PYCODE'
import sys
print('d72cdcff1e22a'+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
