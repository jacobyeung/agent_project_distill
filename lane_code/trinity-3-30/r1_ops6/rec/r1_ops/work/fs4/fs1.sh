#!/bin/bash
# r1_ops4: read-only first-steps peek for 171377 (bounded outputs, redacted).
set +x; set -uo pipefail; export TZ=UTC
KH=/project/community/jjyeung/okh7/x_69d2930d; R=$KH/runs/673bc60f
date -u +%FT%TZ
for f in $R/attempt_171377.json $R/binding.json $KH/o/171377.w.steps $KH/o/171377.3.json; do echo "== $f"; head -c 3000 "$f"; echo; done
echo "== gpu"; tail -c 600 $KH/o/171377.gpu; echo
echo "== runs top"; ls -la --time-style=+%H:%M:%S $R | head -40
echo "== metrics files"; find $R -maxdepth 3 -name '*metric*' -printf '%TT %s %p\n' 2>/dev/null | head
python3 -B - "$R" <<'PYCODE'
import json,sys,glob,re
from pathlib import Path
R=Path(sys.argv[1])
def red(s): return re.sub(r'https?://\S+','[URL]',s)
def tree(x,d=0,maxd=4):
  if d>=maxd: return type(x).__name__
  if isinstance(x,dict): return {k:tree(v,d+1,maxd) for k,v in list(x.items())[:60]}
  if isinstance(x,list): return [len(x), tree(x[0],d+1,maxd) if x else None]
  if isinstance(x,(int,float,bool)) or x is None: return x
  return red(str(x))[:80]
for p in sorted(R.glob('**/metrics*.jsonl'))[:3]:
  print('== M',p,p.stat().st_size)
  with p.open('rb') as f:
    for n,line in enumerate(f):
      if n>=1: break
      try: print(json.dumps(tree(json.loads(line)))[:12000])
      except Exception as e: print('ERR',e)
PYCODE
