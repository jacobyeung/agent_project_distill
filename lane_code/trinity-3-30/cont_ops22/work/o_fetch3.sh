#!/bin/bash
set -euo pipefail
umask 077
S=/project/community/jjyeung/okh7/813f42db/c21a600
read P TOKEN < <(/usr/bin/python3 -I -s -B -c "import json;b=json.load(open('$S/BUILD.json'));assert set(b)=={'A'};print(b['A']['package'],b['A']['token'])")
cd "$P"
JOB=$(cat "$P/a/8.txt")
[[ "$JOB" =~ ^[0-9]+$ ]]
RET=$(/usr/bin/python3 -I -s -B - "$JOB" "$TOKEN" <<'PYCODE'
import sys
print(sys.argv[2]+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B "$P/a/7.py" --package "$P" --return-token "$RET" --out "$P/a/f"
cat $P/a/f/EXIT.json | head -c 700; echo; for f in $P/a/x*; do echo "== $f"; head -3 $f; done
SP=/project/community/jjyeung/okh7/ae71c903; test -d $SP/$RET && ! test -e ${SP}_fetched/$RET && mv $SP/$RET ${SP}_fetched/$RET && echo "moved $RET"; ls -la $P/a/f; du -sb --exclude=e $P
echo ======OWN
( set -euo pipefail; D=/project/community/jjyeung/okh7/a15_cot_ap7e4d49a0f823; P=/project/community/jjyeung/okh7/a15_cot_apfadf2291c654b
cd $D; bash o_fetch.sh; JOB=$(cat $P/a/8.txt); RET=fadf2291c654b$(printf '%08x' $JOB); echo RET $RET
head -c 900 $P/a/f/EXIT.json; echo; for f in $P/a/x*; do echo "== $f"; head -3 $f; done
SP=/project/community/jjyeung/okh7/ae71c903; test -d $SP/$RET && ! test -e ${SP}_fetched/$RET && mv $SP/$RET ${SP}_fetched/$RET && echo "moved $RET"; ls -la $P/a/f; du -sb --exclude=e $P )
