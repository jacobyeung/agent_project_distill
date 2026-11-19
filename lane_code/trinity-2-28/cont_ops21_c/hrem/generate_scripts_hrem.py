"""Generate self-contained streamed Orchard build script and guarded action scripts."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ASSETS=['orchard_hrem.py','make_items_remainder_h.py','build_remainder_h.py','return_tools_h.py','score_base_h.py',
        'score_h_merge.py','heldout_h.py','fetch_validation.py','build_h_base.py','build_support.py','place_fill_hrem.py',
        'dryres_h.py','bind_H200.json','bind_H400.json','bind_H544.json','cpu_guard_hrem.sh','sub_guard_hrem.sh']
HEADER='''#!/bin/bash
set -euo pipefail
umask 077
: "${PARENT:?Set the full parent package path}"
: "${STAGE:?Set 813f42db/c21h544r, c21h200r or c21h400r}"
: "${STEP:?Set 200, 400 or 544}"
KROOT=/project/community/jjyeung/okh7
case "$STEP" in 200|400|544) ;; *) exit 1;; esac
[[ "$PARENT" =~ ^/project/community/jjyeung/okh7/a15_cot_ap[0-9a-f]+$ ]]
case "$STAGE" in 813f42db/*) STAGE="$KROOT/$STAGE";; esac
[[ "$STAGE" =~ ^/project/community/jjyeung/okh7/813f42db/[a-zA-Z0-9_-]+$ ]]
KIT="${STAGE}-kit"
export KROOT OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
/usr/bin/python3 -B -c "import os,sys;s=os.statvfs('$KROOT');f=s.f_bavail*s.f_frsize;print('FREE_GIB %.1f'%(f/1024**3));sys.exit(0 if f>=300*1024**3 else 3)" || { echo "REFUSE: project filesystem under 300 GiB free"; exit 3; }
'''

def generate():
    (HERE/'cpu_guard_hrem.sh').write_bytes((HERE/'in/hcam/o_cpu_H.sh').read_bytes())
    sub=(HERE/'in/hcam/o_sub_H.sh').read_text()
    sub=sub.replace("assert op['COUNTS']==(300,300,300,0,0) and op['SCHEDULE']==((0,0),(0,1),(0,2))", "with tarfile.open(str(p/'0.tgz')) as archive:\n    plan=json.load(archive.extractfile('9.json'))\nassert op['COUNTS']==tuple(plan['remainder']['counts'])\nassert op['SCHEDULE']==tuple(tuple(x) for x in plan['remainder']['schedule'])")
    (HERE/'sub_guard_hrem.sh').write_text(sub)
    assets={}
    for n in ASSETS:
        raw=(HERE/n).read_bytes();assets[n]=dict(sha256=hashlib.sha256(raw).hexdigest(),data=base64.b64encode(gzip.compress(raw,mtime=0)).decode())
    body=HEADER+'''test ! -e "$STAGE"
test ! -e "$KIT"
/usr/bin/python3 -B - "$KIT" <<'PYASSETS'
import base64,gzip,hashlib,json,sys
from pathlib import Path
kit=Path(sys.argv[1]);kit.mkdir(mode=0o700)
assets = '''+repr(assets)+'''
for name,pin in assets.items():
    raw=gzip.decompress(base64.b64decode(pin['data']))
    if hashlib.sha256(raw).hexdigest()!=pin['sha256']:raise ValueError('Embedded asset differs')
    with (kit/name).open('xb') as f:f.write(raw)
PYASSETS
exec /usr/bin/python3 -B "$KIT/orchard_hrem.py" build --parent "$PARENT" --stage "$STAGE" --step "$STEP"
'''
    (HERE/'o_build_hrem.sh').write_text(body)
    resolve='''mapfile -t SEALED < <(/usr/bin/python3 -B "$KIT/orchard_hrem.py" resolve --parent "$PARENT" --stage "$STAGE" --step "$STEP")
test "${#SEALED[@]}" = 2
export P="${SEALED[0]}" T="${SEALED[1]}"
'''
    for action in ('place_fill','cpu','sub','fetch'):
        if action=='place_fill':tail='''export REUSE_PARTS_FROM="$PARENT/a/e"
exec /usr/bin/python3 -B "$KIT/place_fill_hrem.py" --stage "$STAGE" --parent "$PARENT"
'''
        elif action=='fetch':tail='exec /usr/bin/python3 -B "$KIT/orchard_hrem.py" fetch --parent "$PARENT" --stage "$STAGE" --step "$STEP"\n'
        else:tail='exec bash "$KIT/%s_guard_hrem.sh"\n'%action
        (HERE/('o_%s_hrem.sh'%action)).write_text(HEADER+resolve+tail)
if __name__=='__main__':generate()
