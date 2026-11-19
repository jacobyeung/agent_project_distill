"""Embed reviewed code, items and bindings in an Orchard build script (stdlib only)."""
import argparse
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='o_build_H.sh');a=p.parse_args()
    here=Path(__file__).resolve().parent
    files={'b.py':'build_h.py','build_support.py':'build_support.py','heldout_h.py':'heldout_h.py',
           'bind_H200.json':'bind_H200.json','bind_H544.json':'bind_H544.json','bind_H400.json':'bind_H400.json','TIMING_H.json':'TIMING_H.json',
           'place_fill_h.py':'place_fill_h.py','dryres_h.py':'dryres_h.py','score_h.py':'score_h.py','test_score_h.py':'test_score_h.py'}
    assets={n:(here/source).read_bytes() for n,source in files.items()}
    for n in ['HELDOUT_CAMERA_ITEMS.json','HELDOUT_CAMERA_TWINS.json','HELDOUT_NATIVE_TASKS.jsonl','SCORER_PATCH/CHECKS.json','SCORER_PATCH/placement.patch','SCORER_PATCH/h1eval/scorers.py']:assets['in/'+n]=(here/'in'/n).read_bytes()
    text='''#!/bin/bash
# Run on Orchard login. STEP=200, 400 or 544; override SOURCE_1TGZ/SOURCE_SHA256 only together.
set -euo pipefail
umask 077
: "${STAGE:=/project/community/jjyeung/okh7/813f42db/h}"
: "${STEP:=544}"
: "${WALLTIME:=04:00:00}"
: "${SOURCE_1TGZ:=/project/community/jjyeung/okh7/a15_cot_ap2227412cc8721d20/1.tgz}"
: "${SOURCE_SHA256:=dcff106800e96e871a57a58dbb33fe9923beefa575ac668ac1c8e66fd7113459}"
case "$STEP" in 200|400|544) ;; *) echo 'STEP must be 200, 400 or 544' >&2; exit 1;; esac
test ! -e "$STAGE"
mkdir -m 700 "$STAGE"
/usr/bin/python3 -B - "$STAGE" "$STEP" <<'PYASSETS'
import base64,gzip,hashlib,json,sys
from pathlib import Path
stage=Path(sys.argv[1]);step=sys.argv[2]
assets = '''
    def compressed(raw):
        out=io.BytesIO()
        with gzip.GzipFile(fileobj=out,mode='wb',mtime=0) as f:f.write(raw)
        return out.getvalue()
    packed={n:dict(sha256=hashlib.sha256(b).hexdigest(),data=base64.b64encode(compressed(b)).decode()) for n,b in assets.items()}
    text+=repr(packed)+'''\nfor name,spec in assets.items():
    raw=gzip.decompress(base64.b64decode(spec['data']))
    assert hashlib.sha256(raw).hexdigest()==spec['sha256']
    path=stage/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
(stage/'binding.json').write_bytes((stage/('bind_H'+step+'.json')).read_bytes())
PYASSETS
/usr/bin/python3 -B "$STAGE/b.py" "$STAGE" "$SOURCE_1TGZ" "$SOURCE_SHA256" "$STAGE/binding.json" --time "$WALLTIME"
/usr/bin/python3 -B - "$STAGE" <<'PYRESULT'
import json,sys
from pathlib import Path
r=json.loads((Path(sys.argv[1])/'BUILD.json').read_text())['H']
print('token='+r['token'])
print('delivery_dir='+r['delivery_dir'])
print('sha256='+r['delivery_sha256'])
print('walltime='+r['walltime']+' budget_fits='+str(r['budget_fits']))
PYRESULT
'''
    Path(a.out).write_text(text);print(json.dumps(dict(out=a.out,bytes=len(text.encode()),items_sha256=hashlib.sha256(assets['in/HELDOUT_CAMERA_ITEMS.json']).hexdigest())))

if __name__=='__main__':main()
