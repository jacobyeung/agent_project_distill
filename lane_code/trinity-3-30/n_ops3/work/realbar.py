"""Condition C (ORCH 0210Z): test the watcher's bars on the MEASURED first batch.
Usage: realbar.py RAW  (a real mon/raw/* or mon/last.raw holding @@STEP rows of the launch job)
Builds mutated copies of the real raw (extra steps appended after the last real step) and runs parse.py on each
in a fresh state dir under n_ops3/work/realbar/. Prints PASS/FAIL per case; exit 1 on any FAIL."""
import json,sys,os,re,subprocess,copy,math,shutil
W='/scratch/jjyeung/orch_n30/n_ops1/work'; PY='/scratch/jjyeung/envs/p1cpu/bin/python'; D='/scratch/jjyeung/orch_n30/n_ops3/work/realbar'
raw=open(sys.argv[1]).read(); lines=raw.split('\n')
J=lines[lines.index('@@SQ')+1].split('|')[0]
steps=[json.loads(l[7:]) for l in lines if l.startswith('@@STEP ')]
if not steps:sys.exit('no @@STEP rows in '+sys.argv[1])
last=steps[-1]; print('job',J,'real steps',[s['step'] for s in steps],'streams',sorted((last['ranks'][0].get('sm') or {}).keys()),'ranks',len(last['ranks']))
def mk(extra):
  out=[];done=False
  for l in lines:
    out.append(l)
    if l.startswith('@@STEP ') and json.loads(l[7:])['step']==last['step'] and not done:
      out+=['@@STEP '+json.dumps(e) for e in extra];done=True
  return '\n'.join(out)
def mut(n,f,ranks=None):
  s=copy.deepcopy(last);s['step']=last['step']+n
  for k in s['ranks']:
    if ranks is None or k['rank'] in ranks:k['sm']={a:f(v) for a,v in k['sm'].items()}
  return s
NAN=float('nan')
def run(name,seq,expect,absent=(),rc_want=None):
  d=D+'/'+name; os.makedirs(d,exist_ok=True)
  for f in os.listdir(d):os.replace(d+'/'+f,d+'/.'+f+'.prev') if not f.startswith('.') else None
  json.dump({'job':J},open(d+'/state.json','w'))
  for r in seq:
    open(d+'/raw','w').write(r);p=subprocess.run([PY,W+'/parse.py',d+'/raw',d],capture_output=True,text=True);out=p.stdout.strip();rc=p.returncode
    if p.stderr:print(name,'STDERR',p.stderr[-600:])
  ok=all(e in out for e in expect) and not any(a in out for a in absent) and (rc_want is None or rc==rc_want)
  print('PASS' if ok else 'FAIL',name,'rc=%d'%rc,'|',out[-300:]);return ok
st0=sorted(last['ranks'][0]['sm'])
r=[run('real',[raw],['"step":%d'%last['step']],['NONFINITE','STOP_BAR','LOSS3X'])]
r.append(run('nan_one_rank',[mk([mut(1,lambda v:NAN,ranks=[last['ranks'][0]['rank']])])],['NONFINITE step %d'%(last['step']+1)],['STOP_BAR'],2))
r.append(run('nan_all_one_step',[mk([mut(1,lambda v:NAN)])],['NONFINITE'],['STOP_BAR'],2))
r.append(run('stop_bar',[mk([mut(1,lambda v:NAN)]),mk([mut(1,lambda v:NAN),mut(2,lambda v:NAN)])],['STOP_BAR'],(),4))
r.append(run('loss3x',[mk([mut(1,lambda v:v*20)]),mk([mut(1,lambda v:v*20),mut(2,lambda v:v*20)]),mk([mut(1,lambda v:v*20),mut(2,lambda v:v*20),mut(3,lambda v:v*20)])],['LOSS3X_'],()))
print('streams the loss bars know:',[s for s in ('pose','vqa','routing','pointing') if s in st0],'| streams in real rows the bars ignore:',[s for s in st0 if s not in ('pose','vqa','routing','pointing')])
print('ALL PASS' if all(r) else 'SOME FAIL');sys.exit(0 if all(r) else 1)
