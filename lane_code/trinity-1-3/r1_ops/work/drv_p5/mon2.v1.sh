#!/bin/bash
# Read-only status of proof 171335 and canary training 171377 (r1_ops3).
set +x
set -uo pipefail
export TZ=UTC
KH=/project/community/jjyeung/okh7/x_69d2930d
date -u +%FT%TZ
squeue -u "$USER" -h -o '%i|%j|%P|%T|%M|%l|%b|%R' | grep -v '|jjy_' 
sacct -X -n -P -j 171356,171377 -o JobIDRaw,State,ExitCode,Elapsed,NodeList 2>/dev/null
ls -la --time-style=+%H:%M:%S "$KH/o/" | grep -E '171356|171377' | awk '{print $5, $6, $7}'
python3 -B - "$KH" <<'PYCODE'
import re,sys
from pathlib import Path
k=Path(sys.argv[1])
def redact(s):
 s=re.sub(r'https?://[^\s<>\"\x27]+','[URL WITHHELD]',s)
 s=re.sub(r'(?i)Bearer +[^ ,]+','Bearer [WITHHELD]',s)
 s=re.sub(r'ya29[.][A-Za-z0-9._-]+','[TOKEN WITHHELD]',s)
 return re.sub(r'(?i)(authorization|access_token|refresh_token|upload_id|password|secret|token)[\"\x27 	]*[:=][\"\x27 	]*[^\s,}]+',r'\1=[WITHHELD]',s)
for job,sfx,n in (("171356","proof.log",6),("171356","err",4),('171377','err',12),('171377','steps',4),('171377','out',4)):
 p=k/'o'/(job+'.'+sfx)
 if not p.is_file(): print('==',p.name,'NOT_YET'); continue
 with p.open('rb') as f:
  f.seek(max(0,p.stat().st_size-12000)); raw=f.read()
 print('==',p.name,p.stat().st_size); print(redact('\n'.join(l[:300] for l in raw.decode(errors='replace').splitlines()[-n:])))
PYCODE
