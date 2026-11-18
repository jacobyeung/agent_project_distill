export TZ=UTC
umask 077
KH=/project/community/jjyeung/okh7/x_69d2930d
F=$KH/o/171335.canary.reproof.json
[[ ! -e "$F" ]] && printf '%s\n' '{"canary_marker":"171335.canary.json","training_job":"171337","proof_job_attempt1":"171335","attempt1_state":"CANCELLED","proof_job":"171356","proof_partition":"general","utc":"2026-11-18T02:03:07Z","reason":"attempt 1 held the single advanced node per user and blocked the training job"}' > "$F" && echo NOTE_WRITTEN
#!/bin/bash
# Read-only status of proof 171335 and canary training 171337 (r1_ops3).
set +x
set -uo pipefail
export TZ=UTC
KH=/project/community/jjyeung/okh7/x_69d2930d
date -u +%FT%TZ
squeue -u "$USER" -h -o '%i|%j|%P|%T|%M|%l|%b|%R' | grep -v '|jjy_' 
sacct -X -n -P -j 171356,171337 -o JobIDRaw,State,ExitCode,Elapsed,NodeList 2>/dev/null
ls -la --time-style=+%H:%M:%S "$KH/o/" | grep -E '171356|171337' | awk '{print $5, $6, $7}'
python3 -B - "$KH" <<'PYCODE'
import re,sys
from pathlib import Path
k=Path(sys.argv[1])
def redact(s):
 s=re.sub(r'https?://[^\s<>\"\x27]+','[URL WITHHELD]',s)
 s=re.sub(r'(?i)Bearer +[^ ,]+','Bearer [WITHHELD]',s)
 s=re.sub(r'ya29[.][A-Za-z0-9._-]+','[TOKEN WITHHELD]',s)
 return re.sub(r'(?i)(authorization|access_token|refresh_token|upload_id|password|secret|token)[\"\x27 	]*[:=][\"\x27 	]*[^\s,}]+',r'\1=[WITHHELD]',s)
for job,sfx,n in (("171356","proof.log",6),("171356","err",4),('171337','err',12),('171337','steps',4),('171337','out',4)):
 p=k/'o'/(job+'.'+sfx)
 if not p.is_file(): print('==',p.name,'NOT_YET'); continue
 with p.open('rb') as f:
  f.seek(max(0,p.stat().st_size-12000)); raw=f.read()
 print('==',p.name,p.stat().st_size); print(redact('\n'.join(l[:300] for l in raw.decode(errors='replace').splitlines()[-n:])))
PYCODE
