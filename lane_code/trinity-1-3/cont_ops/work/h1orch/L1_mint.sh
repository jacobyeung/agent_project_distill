#!/bin/bash
# Step 8a (run on trinity-1-3 only when main returns GPUs): mint 44 create-only sessions for H1-1. Never prints URIs.
set -euo pipefail; umask 077
W=/scratch/jjyeung/orch_n30/cont_ops/work; OUT=$W/h1orch/sess_17c4ffa4.json
test ! -e $OUT || { echo "OUT exists"; exit 3; }
/usr/bin/python3 -I $W/d0/jobB/mint.py $OUT 8865619b 17c4ffa4 m1 m50 m100 m200 m400 m600 m800 m1000 mstop mstopB mstopC
/usr/bin/python3 -I - $OUT $W/h1/EXPORT_OBJECTS.txt <<'P'
import json,sys
d=json.load(open(sys.argv[1])); want=set(open(sys.argv[2]).read().split())
assert set(d)==want and len(d)==44, ('key mismatch', len(d), len(want))
assert all(v.startswith('https://storage.googleapis.com/upload/') for v in d.values())
print('sessions ok', len(d))
P
stat -c '%a %s' $OUT; sha256sum $OUT | cut -c1-16
