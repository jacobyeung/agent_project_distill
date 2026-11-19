"""n_ops1 alarm tests: synthetic raw checks built from recorded 172660 values (step-600 rank-0 row, P medians) and proof 173236's j.out."""
import json,subprocess,os,shutil,sys,math
W='/scratch/jjyeung/orch_n30/n_review1/nops'; PY='/scratch/jjyeung/envs/p1cpu/bin/python'
JOUT=open(W+'/t1/last.raw').read().split('@@JOUT 12906\n')[1].split('@@JTAIL')[0]
SM={"pose":0.12423441559076309,"vqa":0.06256272686161424,"routing":4.030109835184703e-05,"pointing":0.46920966994366}
def rank(r,sm=None,wall=134.3,ck=0,nf=False):
  return dict(rank=r,wall=wall,data=32.1,skip=0,sm=sm or dict(SM),csum=0.18,gn={"llm":0.86},nf=nf,peak=64282614272,ck=ck,ex=0)
def raw(t,J='99',state='RUNNING',steps=(),qlog=None,tlog=True,cpu=0,anon=50,mx=800,tmp=5000,df=400,others=False,name='a15_cot_ap1a2b3c4d',left='20:00:00',gpu=(90,90,90,90),srun=0,qres='{"status": "ADMIT", "init_milestone": 400}',errs=0,end=True,jout=JOUT):
  s=['@@NOW 2026-11-19T%s'%t,'@@SQ','%s|%s|advanced|%s|3:00:00|1-00:00:00|%s|orchard-community-1|orchard-community-1|x'%(J,name,state,left)]
  if others:s.append('173241|a15_cot_apda6f7936c1779|advanced|RUNNING|0:18|4:00:00|3:59:42|n|n|x')
  s+=['@@NEWEST %s.out'%J,'@@DF %d'%df,'@@SACCT','%s|%s|advanced|%s|0:0|3:00:00|1-00:00:00|x|n|a|b|c'%(J,name,state),'@@SCTL','JobName='+name,'Command=/project/community/jjyeung/okh7/x_22c714e1/j.sh',
     '@@JOUT %d'%len(jout),jout.rstrip('\n'),'@@JTAIL','@@ODIR']
  if state=='RUNNING':
    s+=['@@NODE','@@Q /tmp/q_22c714e1_%s present'%J,'@@TMPDF %d'%tmp,'@@LOG q.log 1000 1','@@LOG rooms.log 10 1','@@LOG t.log %d 1'%(500+100*len(steps) if tlog else -1),'@@LOG j.sh 10 1']
    s+=['@@TAIL q.log','x','@@ERRS q.log %d'%errs]+(['Traceback (most recent call last):'] if errs else [])
    if qres:s.append('@@QRES '+qres)
    s+=['@@PROG','@@PCOUNT 100','@@MP /tmp/q/x/runs/r/metrics_%s.jsonl'%J if steps else '@@MP -']
    for st in steps:s.append('@@STEP '+json.dumps(st))
    s+=['@@CK','@@CG /sys/fs/cgroup/job max=%d cur=1 anon %d file 1 shmem 0 cpu_usec=%d'%(mx*2**30,anon*2**30,cpu),'@@GPU']+['%d, %d, 70000, 81559'%(i,g) for i,g in enumerate(gpu)]+['@@PS','@@SRUN rc=%d'%srun]
  s+=['@@EXTRA']+(['@@END'] if end else [])
  return '\n'.join(s)+'\n'
def step(n,**kw):
  rs=kw.pop('ranks',None); return dict(step=n,ranks=rs or [rank(i,**kw) for i in range(4)],top_nf=False)
NAN=float('nan')
def run(name,seq,expect,absent=()):
  d=W+'/tests/s_'+name; os.makedirs(d,exist_ok=True)
  for f in ('state.json','steps.jsonl'):
    if os.path.exists(d+'/'+f):os.replace(d+'/'+f,d+'/'+f+'.prev')
  json.dump({'job':'99'},open(d+'/state.json','w'))
  out=''
  for i,r in enumerate(seq):
    open(d+'/raw','w').write(r); p=subprocess.run([PY,W+'/parse.py',d+'/raw',d],capture_output=True,text=True); out=p.stdout.strip(); rc=p.returncode
    if p.stderr:print(name,'STDERR',p.stderr[-800:])
  ok=all(e in out for e in expect) and not any(a in out for a in absent)
  print(('PASS' if ok else 'FAIL'),name,'rc=%d'%rc,'|',out[-330:]); return ok
T=lambda m,s=0:'17:%02d:%02dZ'%(m,s)
H=lambda h,m:'%02d:%02d:00Z'%(h,m)
res=[]
res.append(run('healthy',[raw(T(0),steps=[step(1)],cpu=0),raw(T(1),steps=[step(1),step(2)],cpu=60e6*8)],['"step":2','"stage":"training"'],['FLAG']))
res.append(run('failed_state',[raw(T(0),state='FAILED')],['STATE_FAILED']))
res.append(run('timeout_state',[raw(T(0),state='TIMEOUT')],['STATE_TIMEOUT']))
res.append(run('nonfinite_one_rank',[raw(T(0),steps=[step(1,ranks=[rank(0,sm=dict(SM,vqa=NAN))]+[rank(i) for i in (1,2,3)])])],['NONFINITE step 1 ranks [0]'],['STOP_BAR']))
allnan=lambda n:step(n,ranks=[rank(i,sm=dict(SM,pose=NAN),nf=True) for i in range(4)])
res.append(run('stop_bar',[raw(T(0),steps=[allnan(5)]),raw(T(1),steps=[allnan(5),allnan(6)])],['STOP_BAR']))
res.append(run('stop_single_step_no_stop',[raw(T(0),steps=[allnan(5)])],['NONFINITE'],['STOP_BAR']))
hi=lambda n:step(n,sm=dict(SM,vqa=0.25))
res.append(run('loss3x',[raw(T(0),steps=[hi(1)]),raw(T(1),steps=[hi(1),hi(2)]),raw(T(2),steps=[hi(2),hi(3)])],['LOSS3X_vqa']))
res.append(run('slow',[raw(T(0),steps=[step(1),step(2)]),raw(T(1),steps=[step(2),step(3,wall=420)])],['SLOW step 3']))
res.append(run('slow_ckpt_exempt',[raw(T(0),steps=[step(1),step(2)]),raw(T(1),steps=[step(2),step(3,wall=420,ck=65)])],['"step":3'],['SLOW']))
res.append(run('time_left',[raw(T(0),steps=[step(1),step(2),step(3)],left='5:00:00')],['TIME: step 200']))
res.append(run('disk_project',[raw(T(0),df=120)],['PROJECT_DISK<150G']))
res.append(run('disk_node',[raw(T(0),tmp=200)],['NODE_TMP<300G']))
res.append(run('mem',[raw(T(0),anon=760,mx=800)],['MEM>90%']))
res.append(run('adv_others',[raw(T(0),others=True),raw(T(6),others=True)],['ADV_OTHERS']))
res.append(run('adv_others_grace',[raw(T(0),others=True)],['adv_others'],['ADV_OTHERS']))
res.append(run('nameword',[raw(T(0),name='a15_cot_apdistill1')],['NAMEWORD']))
res.append(run('nameform',[raw(T(0),name='myjob_1')],['NAMEFORM']))
res.append(run('empty_twice',[raw(T(0),end=False),raw(T(1),end=False)],['READLOGS']))
res.append(run('empty_once',[raw(T(0),end=False)],['EMPTY1'],['READLOGS']))
res.append(run('logerr',[raw(T(0),errs=1)],['LOGERR_q.log']))
res.append(run('not_admit',[raw(T(0),qres='{"status": "REFUSED", "reason": "x"}')],['NOT_ADMIT']))
res.append(run('srun_fail',[raw(T(0),srun=1),raw(T(1),srun=1)],['SRUN_FAIL']))
res.append(run('gpu_idle',[raw(T(0),steps=[step(1)],gpu=(0,0,0,0)),raw(T(1),steps=[step(1)],gpu=(0,0,0,0))],['GPU_IDLE']))
st=[raw(T(m),cpu=m*60*0.2e6) for m in range(0,12)]
res.append(run('stall_idle',st,['STALL']))
st=[raw(T(m),cpu=m*60*8e6) for m in range(0,12)]
res.append(run('busy_no_stall',st,['"cores":8.0'],['STALL']))
res.append(run('no_new_step',[raw(T(0),steps=[step(1)],cpu=0)]+[raw(T(m),steps=[step(1)],cpu=m*60*8e6) for m in range(1,17)],['NO_NEW_STEP']))
res.append(run('jout_err',[raw(T(0),jout=JOUT+'Traceback (most recent call last):\nRuntimeError: E42\n')],['JOUT_ERR']))
res.append(run('otar_err',[raw(T(0),state='FAILED').replace('@@ODIR','@@ODIR\n@@OTAR\n{"proof_rc": 1}\nValueError: Missing or changed pinned input: /x')],['OTAR_ERR']))
wr=lambda t,nr='':raw(t).replace('@@ODIR','@@LIVE\n-rw------- 1 u g 60 19:00:00 WAITING_REVIEW\n@@NR\n'+nr+'@@ODIR')
res.append(run('waiting_review',[wr(T(0))],['WAITING_REVIEW'],['NO_REVIEW_30MIN']))
res.append(run('no_review_30',[wr(T(0)),wr(T(31))],['NO_REVIEW_30MIN']))
res.append(run('review_present',[wr(T(0)),wr(T(31),'-rw------- 1 u g 300 19:20:00 review.json\n')],['WAITING_REVIEW'],['NO_REVIEW_30MIN']))
res.append(run('gcs_done',[raw(T(0)).replace('@@ODIR','@@LIVE\n-rw------- 1 u g 107 19:00:00 gcs_m100.done\n@@ODIR')],['NEW_GCS_DONE m100']))
print('ALL PASS' if all(res) else 'SOME FAIL', sum(res),'/',len(res))
