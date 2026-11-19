"""Embed reviewed code, items and bindings in an Orchard build script (stdlib only)."""
import argparse
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('items');p.add_argument('--out',default='o_build_D.sh');a=p.parse_args()
    here=Path(__file__).resolve().parent
    files={'b.py':'build_d.py','build_support.py':'build_support.py','make_items_d.py':'make_items_d.py',
           'bind_D200.json':'bind_D200.json','bind_D544.json':'bind_D544.json','bind_D400.json':'bind_D400.json','TIMING_D.json':'TIMING_D.json',
           'place_fill_d.py':'place_fill_d.py','dryres_d.py':'dryres_d.py','score_d.py':'score_d.py'}
    assets={n:(here/source).read_bytes() for n,source in files.items()};assets['items/dist580.json']=Path(a.items).read_bytes()
    text='''#!/bin/bash
# Run on Orchard login. STEP=200, 400 or 544; override SOURCE_1TGZ/SOURCE_SHA256 only together.
set -euo pipefail
umask 077
: "${STAGE:=/project/community/jjyeung/okh7/813f42db/d}"
: "${STEP:=200}"
: "${WALLTIME:=04:00:00}"
: "${SOURCE_1TGZ:=/project/community/jjyeung/okh7/a15_cot_ap4e8c539166092f0c/1.tgz}"
: "${SOURCE_SHA256:=c3187ab9f88b3eb5a7ab1e30a8010e4ef86acb49d6c76e98fd97eec393b4e45a}"
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
(stage/'binding.json').write_bytes((stage/('bind_D'+step+'.json')).read_bytes())
PYASSETS
/usr/bin/python3 -B "$STAGE/b.py" "$STAGE" "$SOURCE_1TGZ" "$SOURCE_SHA256" "$STAGE/items/dist580.json" "$STAGE/binding.json" --time "$WALLTIME"
/usr/bin/python3 -B - "$STAGE" <<'PYRESULT'
import json,sys
from pathlib import Path
r=json.loads((Path(sys.argv[1])/'BUILD.json').read_text())['D']
print('token='+r['token'])
print('delivery_dir='+r['delivery_dir'])
print('sha256='+r['delivery_sha256'])
print('walltime='+r['walltime']+' budget_fits='+str(r['budget_fits']))
PYRESULT
'''
    Path(a.out).write_text(text);print(json.dumps(dict(out=a.out,bytes=len(text.encode()),items_sha256=hashlib.sha256(assets['items/dist580.json']).hexdigest())))

if __name__=='__main__':main()
