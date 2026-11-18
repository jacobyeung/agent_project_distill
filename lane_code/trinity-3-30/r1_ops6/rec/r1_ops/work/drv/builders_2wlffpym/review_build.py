"""Build rv1.sh from two exact-packet GO verdicts. Never infer missing approval."""
import argparse,hashlib,json,re
from pathlib import Path
W=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--r1p',type=Path,default=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_r1p/REVIEW_VERDICT_R1P.md'));p.add_argument('--r1p2',type=Path,default=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_r1p2/REVIEW_VERDICT_R1P2.md'));a=p.parse_args()
identity='782f303d81e300b1b24094863d6ce7d984690529f0e414474c3e693df87e19da';tree='b7d19ec090bcab112ed0ce72758e4491e02aff14d4645ac3945bb56ebd7d379e';outer='42bbcbb218c982b4e33cc92c7be97f01359ae2e47cd20e387c0008edefc6b1cb'
reviews={};texts={}
for name,path,short in [('review_r1p',a.r1p,'r1.txt'),('review_r1p2',a.r1p2,'r2.txt')]:
 if not path.is_file():raise SystemExit('PENDING: missing '+name)
 raw=path.read_bytes();s=raw.decode();header=next((x for x in s.splitlines() if x.strip()),'')
 if not re.search(r'\bGO\b',header) or re.search(r'NO.GO|AFTER|PENDING|CONDITIONAL',header,re.I):raise SystemExit('PENDING: '+name+' must state unconditional GO on its first nonblank line')
 if not all(x in s for x in (identity,tree,outer)):raise SystemExit('PENDING: '+name+' must name the full final config, tree and outer archive hashes')
 reviews[name]=dict(verdict='GO',sha256=hashlib.sha256(raw).hexdigest(),file=short)
 texts[short]=s
record=dict(config_sha256=identity,source_revision='sha256:'+tree,operator_archive_sha256=outer,reviews=reviews)
body='''#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
python3 -B - <<'PYCODE'
import json,os
from pathlib import Path
b=Path('/project/community/jjyeung/okh7/i_1130b378')
assert b.is_dir() and not b.is_symlink() and b.stat().st_mode & 0o777 == 0o700
'''
body+='texts='+repr(texts)+'\nrecord='+repr(record)+'\n'
body+='''for n,t in texts.items():
 with (b/n).open('x') as f:f.write(t)
with (b/'r1.json').open('x') as f:json.dump(record,f,sort_keys=True);f.write('\\n')
print('PASS installed two exact-packet GO verdicts; no production GO granted')
PYCODE
'''
with (W/'rv1.sh').open('x') as f:f.write(body)
(W/'rv1.sh').chmod(0o700)
print('READY rv1.sh; two exact-packet GO verdicts pinned')
