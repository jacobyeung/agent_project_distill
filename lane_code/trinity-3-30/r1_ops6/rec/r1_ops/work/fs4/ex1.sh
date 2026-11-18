#!/bin/bash
# r1_ops4: read-only check of 171377's export m100 on pool and GCS markers (redacted).
set +x; set -uo pipefail; export TZ=UTC
KH=/project/community/jjyeung/okh7/x_69d2930d; R=$KH/runs/673bc60f; STEP=${1:-100}
date -u +%FT%TZ
ls -la --time-style=+%H:%M:%S $R/m$STEP/ 2>&1 | head
ls -la --time-style=+%H:%M:%S $KH/o/ | grep -i -E "gcs|m$STEP|export" | awk '{print $5,$6,$7}'
for f in $KH/o/gcs_673bc60f_m$STEP.done; do echo "== $f"; head -c 3000 "$f" 2>&1 | sed -E 's#https?://[^ "]+#[URL]#g'; echo; done
python3 -B - "$R/m$STEP/artifact.json" <<'PYCODE'
import json,sys,os,re
a=json.load(open(sys.argv[1]))
s=json.dumps(a); s=re.sub(r'https?://[^"\s]+','[URL]',s)
print(s[:6000])
# existence/size of every path-like value
def walk(x,p=''):
  if isinstance(x,dict):
    for k,v in x.items(): walk(v,p+'.'+k)
  elif isinstance(x,list):
    for i,v in enumerate(x): walk(v,p+'[%d]'%i)
  elif isinstance(x,str) and x.startswith('/'):
    try: st=os.stat(x); print('PATH',p,x,'exists',st.st_size)
    except OSError as e: print('PATH',p,x,'MISSING',e.__class__.__name__)
walk(a)
PYCODE
