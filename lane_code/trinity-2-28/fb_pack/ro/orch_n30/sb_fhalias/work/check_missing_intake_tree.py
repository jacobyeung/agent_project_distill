"""Import an actual derived source tree with its frame-host intake check removed."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
W=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1]).resolve();label=sys.argv[2]
mutant=W/'work'/('missing_intake_'+label)
inputs={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
inputs[str(W/'work/run.sh')]=sha(W/'work/run.sh')
for p in sorted(source.rglob('*')):
 if p.is_file():inputs[str(p)]=sha(p)
shutil.copytree(source,mutant)
p=mutant/'student_pilot/r2_intake.py'
s=p.read_text()
lookup="os.environ.get(env_key('STUDENT_R2_FRAME_HOST')) == '1'" if 'env_key' in s else "os.environ.get('STUDENT_R2_FRAME_HOST') == '1'"
assert s.count(lookup)==1
p.write_text(s.replace(lookup,'True'))
sys.path.insert(0,str(mutant))
import torch
torch.set_num_threads(8);torch.set_num_interop_threads(1)
from launch_r2.runtime import obligations
from student_pilot import r2_intake
assert Path(r2_intake.__file__).resolve()==p
assert 'STUDENT_R2_FRAME_HOST' not in p.read_text()
try:
 records=obligations();refused=False;error=None
except ValueError as e:
 refused=True;error=str(e)
 assert error=='Statement obligation is ambiguous or absent'
assert refused==('env_key' in s),(label,refused)
for f in sorted(mutant.rglob('*')):
 if f.is_file():inputs[str(f)]=sha(f)
(W/'out'/('missing_intake_'+label+'.json')).write_text(json.dumps(dict(input_sha256=inputs,source=str(source),mutant=str(mutant),removed=lookup,tests=1,successful=True,refused=refused,error=error),indent=2)+'\n')
print('PASS',label,'missing intake check refused:',refused)
