import json,os,signal,time
from pathlib import Path
from datetime import datetime,timezone
R=Path(os.environ['R1315_RUNTIME'])
ROOT=Path('/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/collection_gt_r1313')
PKG=Path('/home/jjyeung/agent_project_distill/collector')
OUT=R
UID=25409
def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def identity(pid):
 try:
  p=Path('/proc')/str(pid);s=(p/'stat').read_text().split();return dict(pid=int(pid),uid=p.stat().st_uid,start_ticks=s[21],state=s[2],args=[x.decode() for x in (p/'cmdline').read_bytes().split(b'\0') if x])
 except (OSError,UnicodeError):return None
def alive(p):
 q=identity(p['pid']);return q and q['start_ticks']==p['start_ticks'] and q['state']!='Z'
def signal_exact(p,sig):
 q=identity(p['pid'])
 if q and q['start_ticks']==p['start_ticks'] and q['state']!='Z':
  assert q['uid']==UID and q['args']==p['args'];os.kill(p['pid'],sig)
def processes():
 result=[]
 for d in Path('/proc').iterdir():
  if not d.name.isdigit():continue
  p=identity(d.name)
  if not p or p['uid']!=UID or p['state']=='Z':continue
  a=p['args']
  packages=[PKG,Path('/home/jjyeung/agent_project/agent/rounds/candidates/r1315_vsi_distill_gt_training_tolerant_sparse'),Path('/home/jjyeung/agent_project_r1313_gt_teacher/agent/rounds/candidates/r1313_vsi_distill_gt_training'),Path('/home/jjyeung/agent_project/agent/rounds/candidates/r1314_vsi_distill_gt_training_tolerant_pool')]
  if any(str(pkg/'collect.py') in a for pkg in packages) and any(x in a for x in ('start','worker')):
   cfg=json.loads(Path(a[a.index('--config')+1]).read_text())
   if cfg['run_root']==str(ROOT):result.append(p)
  elif any(str(pkg/'run_experiment_r1313.py') in a for pkg in packages) and any(x.startswith(str(ROOT/'attempts')+'/') for x in a):result.append(p)
 return result
def terms():return len(list((ROOT/'terminals').glob('*.json')))
