"""Embed reviewed code and binding in an Orchard build script (stdlib only)."""
import argparse
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='o_build_E.sh');a=p.parse_args()
    here=Path(__file__).resolve().parent
    files={'b.py':'build_e.py','build_support.py':'build_support.py',
           'bind_E200.json':'bind_E200.json','TIMING_E.json':'TIMING_E.json',
           'place_fill_e.py':'place_fill_e.py','dryres_e.py':'dryres_e.py','score_e.py':'score_e.py'}
    assets={n:(here/source).read_bytes() for n,source in files.items()}
    text='''#!/bin/bash
# Run on Orchard login. override SOURCE_1TGZ/SOURCE_SHA256 only together.
set -euo pipefail
umask 077
: "${STAGE:=/project/community/jjyeung/okh7/813f42db/e}"
: "${WALLTIME:=02:00:00}"
: "${SOURCE_1TGZ:=/project/community/jjyeung/okh7/a15_cot_ap2227412cc8721d20/1.tgz}"
: "${SOURCE_SHA256:=dcff106800e96e871a57a58dbb33fe9923beefa575ac668ac1c8e66fd7113459}"
test ! -e "$STAGE"
mkdir -m 700 "$STAGE"
/usr/bin/python3 -B - "$STAGE" <<'PYASSETS'
import base64,gzip,hashlib,json,sys
from pathlib import Path
stage=Path(sys.argv[1])
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
(stage/'binding.json').write_bytes((stage/'bind_E200.json').read_bytes())
PYASSETS
/usr/bin/python3 -B "$STAGE/b.py" "$STAGE" "$SOURCE_1TGZ" "$SOURCE_SHA256" "$STAGE/binding.json" --time "$WALLTIME"
/usr/bin/python3 -B - "$STAGE" <<'PYRESULT'
import json,sys
from pathlib import Path
r=json.loads((Path(sys.argv[1])/'BUILD.json').read_text())['E']
print('token='+r['token'])
print('delivery_dir='+r['delivery_dir'])
print('sha256='+r['delivery_sha256'])
print('walltime='+r['walltime']+' budget_fits='+str(r['budget_fits']))
PYRESULT
'''
    Path(a.out).write_text(text);print(json.dumps(dict(out=a.out,bytes=len(text.encode()))))

if __name__=='__main__':main()
