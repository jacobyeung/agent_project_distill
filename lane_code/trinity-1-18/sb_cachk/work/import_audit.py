"""Build the CPU model while rejecting any attempted NFS file access before it occurs."""
from pathlib import Path
import sys,os,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
opened=set(); refused=[]
def audit(event,args):
 if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
  p=os.path.abspath(os.fsdecode(args[0]))
  if p.startswith(('/home/','/data')):
   refused.append(p);raise PermissionError('NFS ACCESS FORBIDDEN: '+p)
  if event=='open' and str(p).startswith('/scratch/'):opened.add(p)
sys.addaudithook(audit)
sys.path.insert(0,str(ROOT/'kit_v2'))
import mc_common as C
import torch
torch.set_num_threads(8)
import mc_tracker as T
error=None;model=None
try:model=T.Sam3Carry('cpu')
except Exception as e:error=repr(e)
st=json.loads((ROOT/'out/v2/STAGING.json').read_text())
roots=[Path(p) for i in st['items'] for p in (i['path'] if isinstance(i['path'],list) else [i['path']])]
# C.TOWER is the documented CPU-only adaptation, never used by the GPU path.
outside=sorted(p for p in opened if Path(p)!=Path(__file__) and not any(Path(p)==r or r in Path(p).parents for r in roots))
C.code_pins();C.pin(__file__);C.pin(ROOT/'out/v2/STAGING.json')
for p in [Path('/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages/__editable___sam3_0_1_0_finder.py'),Path('/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages/__editable__.sam3-0.1.0.pth')]:C.pin(p)
C.write_json(ROOT/'out/check/IMPORT_AUDIT.json',dict(command='bash kit_v2/run_cpu.sh sam3 ../work/import_audit.py',
 error=error,nfs_attempts=refused,nonlocal_modules=model.outside if model else None,opened_outside_staging=outside,
 note='The editable finder has stale /home mappings; this run tests whether the pinned local source shadows them. CPU-only sam3_tower is outside GPU staging by design.',
 parameters=sum(p.numel() for p in model.model.parameters()) if model else None))
print(json.dumps(dict(error=error,nfs_attempts=refused,nonlocal_modules=model.outside if model else None,opened_outside_staging=outside),indent=2))
if error or refused:sys.exit(1)
