"""Build rv1.sh only from the complete final-packet independent review chain."""
import argparse,json
from pathlib import Path
from packet_config import PINS, render
from review_policy import REVIEWERS, REVIEW_FILES, build_chain
W=Path(__file__).resolve().parent
EVENTS=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events')
p=argparse.ArgumentParser()
for option,name,filename in zip(('r1p','r1p2','r1p3'),REVIEWERS,('REVIEW_VERDICT_R1P.md','REVIEW_VERDICT_R1P2.md','REVIEW_VERDICT_R1P3.md')):
 p.add_argument('--'+option,type=Path,default=EVENTS/name/filename)
a=p.parse_args()
texts={}
for option,name,short in zip(('r1p','r1p2','r1p3'),REVIEWERS,REVIEW_FILES):
 path=getattr(a,option)
 if not path.is_file():raise SystemExit('PENDING: missing '+name)
 texts[short]=path.read_bytes().decode()
try:record=build_chain(texts,PINS['identity'],PINS['tree'],PINS['outer'])
except ValueError as error:raise SystemExit('PENDING: '+str(error))
for note in record['nonblocking_fixes']:print('OPERATOR LOW NON-BLOCKING: '+note)
body="""#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
python3 -B - <<'PYCODE'
import hashlib,json,os
from pathlib import Path
b=Path('@BUNDLE@')
assert b.is_dir() and not b.is_symlink() and b.stat().st_mode & 0o777 == 0o700
"""
body+='texts='+repr(texts)+'\nrecord='+repr(record)+'\n'
body+="""for n in list(texts)+['r1.json']:
 assert not (b/n).exists() and not (b/n).is_symlink(), 'REFUSED: review destination exists'
assert json.loads((b/'BINDING.json').read_text())['config_identity']==record['config_sha256']
assert hashlib.sha256((b/'p.tar').read_bytes()).hexdigest()==record['operator_archive_sha256']
for n,t in texts.items():
 with (b/n).open('x') as f:f.write(t)
 (b/n).chmod(0o600)
with (b/'r1.json').open('x') as f:json.dump(record,f,sort_keys=True);f.write('\\n')
(b/'r1.json').chmod(0o600)
for note in record['nonblocking_fixes']:print('OPERATOR LOW NON-BLOCKING: '+note)
print('PASS installed three-review chain; final review_r1p3 accepted for exact packet; no production GO granted')
PYCODE
"""
target=W/'rv1.sh';expected=render(body)
if target.is_symlink():raise SystemExit('REFUSED: linked rv1.sh')
if target.exists():
 if target.read_text()!=expected:raise SystemExit('REFUSED: existing rv1.sh differs from the current review chain')
else:
 with target.open('x') as f:f.write(expected)
target.chmod(0o700)
print('READY rv1.sh; three-review chain pinned; final verdict '+record['final_verdict'])
