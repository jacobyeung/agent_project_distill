#!/bin/bash
set -euo pipefail
umask 077
D=$(cd -- "$(dirname -- "$0")" && pwd)
P=/project/community/jjyeung/okh7/a15_cot_apab0123456789
JOB=$(cat "$P/a/8.txt")
[[ "$JOB" =~ ^[0-9]+$ ]]
RET=$(/usr/bin/python3 -I -s -B - "$P" "$JOB" <<'PY'
import json,sys
from pathlib import Path
print(json.loads((Path(sys.argv[1])/'0.json').read_text())['token']+format(int(sys.argv[2]),'08x'))
PY
)
(cd "$P" && /usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f")
