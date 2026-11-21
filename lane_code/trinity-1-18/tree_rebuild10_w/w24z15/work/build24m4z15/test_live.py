import json,os,subprocess,sys,time
from pathlib import Path
from unittest.mock import patch
J=Path.cwd();D=J/'work/build24m4z15';F=D/'live';F.mkdir()
s=(J/'out/jd8.sh').read_text();code=s.split("<<'PYJ8' || true\n",1)[1].split('\nPYJ8',1)[0]
C=F/'cg';job=C/'slurm/job_123';step=job/'step_batch';leaf=step/'task_0';leaf.mkdir(parents=True)
proc=F/'cgroup';proc.write_text('0::/slurm/job_123/step_batch/task_0\n')
for i,p in enumerate((job,step,leaf)):
 for name,val in {'memory.current':100+i,'memory.max':800*1024**3,'memory.peak':110+i,'memory.events':'low 0\nhigh 0\nmax 1\noom 2\noom_kill 1','memory.stat':'anon 10\nfile 20\nshmem 30\nfile_dirty 40\nfile_writeback 50\nkernel 60\nslab 70'}.items():(p/name).write_text(str(val)+'\n')
code=code.replace('Path("/proc/self/cgroup")',f'Path({str(proc)!r})').replace('Path("/sys/fs/cgroup")',f'Path({str(C)!r})')
(D/'LIVE_EXTRACTED.py').write_text(code+'\n')
node=F/'n';(node/'ev/live').mkdir(parents=True);err=F/'s.err'
for p in (node/'ev/q.log',node/'ev/q.steps',err):p.write_bytes(b'x'*80000+b'end\n')
target=F/'o';moves=[];peak=[0];real_run=subprocess.run
expected={}
def run(argv,*args,**kwargs):
 if 'mv' in argv:
  src,dst=map(Path,argv[-2:]);assert src.name==dst.name+'.part'
  raw=src.read_bytes();before=dst.read_bytes() if dst.exists() else None
  total=sum(p.stat().st_size for p in target.rglob('*') if p.is_file());peak[0]=max(peak[0],total);assert total<4_000_000
  result=real_run(argv,*args,**kwargs)
  assert dst.read_bytes()==raw and not src.exists();moves.append(dict(name=dst.name,bytes=len(raw),replaced=before is not None,total=total))
  return result
 return real_run(argv,*args,**kwargs)
def snap(phase='live'):
 with patch.object(sys,'argv',['-',str(node),str(target),'123',str(err),phase]),patch('subprocess.run',run):exec(compile(code,'jd8-PYJ8','exec'),{'__name__':'__main__'})
 assert not list(target.glob('*.part'))
 return json.loads((target/'live.json').read_bytes())
r=snap();assert r['once']=={}
assert target.stat().st_mode&0o777==0o700
mem=(target/'mem.txt').read_text();assert all(s in mem for s in ('job '+str(job),'step '+str(step),'leaf '+str(leaf),'anon 10','kernel 60','oom_kill 1')) and 'slab 70' not in mem
for name,p in [('q.log',node/'ev/q.log'),('q.steps',node/'ev/q.steps'),('s.err',err)]:assert (target/name).read_bytes()==p.read_bytes()[-65536:]
assert str(node) not in (target/'df.txt').read_text() or (target/'df.txt').stat().st_size>0
# The first two fit; the third cannot fit alongside them, even during .part writes.
for n in ('v.json','WAITING_REVIEW.json','f1.json'):(node/'ev/live'/n).write_bytes(b' '*1_490_000)
r=snap();assert r['once']['v.json']['copied'] and r['once']['WAITING_REVIEW.json']['copied']
assert r['once']['f1.json']=={'bytes':1_490_000,'copied':False,'reason':'budget'}
old=(target/'v.json').read_bytes();(node/'ev/live/v.json').write_text('changed')
(node/'j2.log').write_text('work exit 7\n');ended=time.time_ns();r=snap('final')
assert r['phase']=='final' and r['time_ns']>=ended and (target/'v.json').read_bytes()==old
assert sum(p.stat().st_size for p in target.rglob('*') if p.is_file())<4_000_000
# Oversized one-shot files are recorded by size only, including at the boundary.
target=F/'large';(node/'ev/live/v.json').write_bytes(b'x'*1_500_000)
(node/'ev/live/WAITING_REVIEW.json').write_bytes(b'x'*1_500_001)
r=snap();assert not (target/'v.json').exists() and not (target/'WAITING_REVIEW.json').exists()
assert r['once']['v.json']['reason']=='size' and r['once']['WAITING_REVIEW.json']['bytes']==1_500_001
result=dict(status='OK',atomic_moves=len(moves),max_bytes_including_parts=peak[0],mode_700=True,job_step_leaf=True,tails=3,once=True,oversize=True,budget_skip=True,final_after_work_exit=True)
(D/'LIVE_TESTS.json').write_text(json.dumps(result,indent=2)+'\n');(D/'LIVE_MOVES.json').write_text(json.dumps(moves,indent=2)+'\n');print(json.dumps(result))
