"""n_ops1 parser: one raw Orchard check (stdin, @@-sections) + mon/state.json -> summary line, flags, steps.jsonl.
Usage: parse.py RAW STATE_DIR. Exit 0 ok, 2 ALARM (BLOCKER-worthy), 4 STOP (non-finite on every rank, two consecutive steps)."""
import json,math,re,sys,os,time,statistics as st
from datetime import datetime,timezone
raw=open(sys.argv[1]).read(); D=sys.argv[2]
SP=os.path.join(D,'state.json'); S=json.load(open(SP)) if os.path.exists(SP) else {}
BASE={'pose':0.148,'vqa':0.0590,'pointing':0.43}      # P (job 172660) four-rank medians near step 400; pointing from A's steps 186-200
MAD={'pose':0.009,'vqa':0.0015,'pointing':0.045}
WORDS=["split","distill","revsi","vsi","vsibench","vsti","sti","mindcube","scannet","arkit","qwen","qgen","gf1","geometry","benchmark","dataset","student","teacher","trace","resti","sam3","g3t","vggt"]
J=S.get('job','0'); flags=[]; warn=[]; info={}
def sec(name):
  m=re.search(r'^@@'+name+r'\b(.*?)$\n?(.*?)(?=^@@|\Z)',raw,re.M|re.S); return (m.group(1).strip(),m.group(2)) if m else (None,'')
def parse_t(s):
  try:return datetime.strptime(s,'%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc).timestamp()
  except Exception:return None
def dur(s):  # slurm [D-]HH:MM:SS or MM:SS
  if not s or s in ('INVALID','UNLIMITED','NOT_SET'):return None
  d=0
  if '-' in s:a,s=s.split('-');d=int(a)
  p=[int(x) for x in s.split(':')];p=[0]*(3-len(p))+p
  return d*86400+p[0]*3600+p[1]*60+p[2]
now_s,_=sec('NOW'); ended=sec('END')[0] is not None
if not ended or not now_s:
  S['empty']=S.get('empty',0)+1; flags.append('EMPTY%d'%S['empty'])
  if S['empty']>=2:flags.append('READLOGS')
  json.dump(S,open(SP,'w'));print(time.strftime('%H:%M:%SZ',time.gmtime()),'EMPTY check',S['empty'],'FLAG '+' '.join(flags));sys.exit(2 if S['empty']>=2 else 0)
S['empty']=0; now=parse_t(now_s[:19])
# queue
sq=[l.split('|') for l in sec('SQ')[1].splitlines() if l.count('|')>=8]
adv=[q for q in sq if q[2]=='advanced']
info['newest_out']=sec('NEWEST')[0]; dfp=int(sec('DF')[0] or 0); info['proj_free_G']=dfp
if dfp and dfp<150:flags.append('PROJECT_DISK<150G')
elif dfp and dfp<250:warn.append('project_free<250G')
mine=[q for q in sq if q[0]==J]
state=mine[0][3] if mine else None
sa=[l.split('|') for l in sec('SACCT')[1].splitlines() if '|' in l]
if sa:info['sacct']=sa[0][3]; state=state or sa[0][3]
info['state']=state
if J!='0':
  if state not in ('PENDING','RUNNING','CONFIGURING','COMPLETING'):flags.append('STATE_'+str(state))
  others=[q[0]+':'+q[1] for q in adv if q[0]!=J]
  if others and state in ('RUNNING','PENDING') and not os.path.exists(os.path.join(D,'noadv')):  # mon/noadv: job not on advanced (discovery run)
    S.setdefault('others_since',now); 
    if now-S['others_since']>300:flags.append('ADV_OTHERS '+','.join(others))
    else:warn.append('adv_others '+','.join(others))
  else:S.pop('others_since',None)
  sc=dict(l.split('=',1) for l in sec('SCTL')[1].splitlines() if '=' in l)
  hit=[(k,w) for k in ('JobName','Command','WorkDir','StdOut','StdErr') for w in WORDS if w in sc.get(k,'').lower()]
  if hit:flags.append('NAMEWORD '+str(hit))
  if sc.get('JobName') and not re.fullmatch(r'a15_cot_ap[0-9a-f]+',sc['JobName']):flags.append('NAMEFORM '+sc['JobName'])
  if mine:
    el=dur(mine[0][4]);lim=dur(mine[0][5]);left=dur(mine[0][6]);info.update(node=mine[0][8],elapsed=mine[0][4],limit=mine[0][5],left=mine[0][6])
    if state=='PENDING':info['reason']=mine[0][7]
  else:left=None
  if state=='PENDING' and 'held' in str(info.get('reason','')).lower():  # 24m4z: sbatch --hold until n_ops mints sess_<job>.json (ORCH 2058Z: normal up to 15 min)
    S.setdefault('held_since',now); m=(now-S['held_since'])/60; info['held_min']=round(m)
    if m>=15:flags.append('HELD %d min'%m)
    else:warn.append('held %d min'%m)
  else:S.pop('held_since',None)
  # stage from j.out
  jo=sec('JOUT'); jtxt=jo[1]; jsz=int((jo[0] or '-1').split()[0])
  stage='submitted'
  for pat,name in [(r'gpu0:','started'),(r'resolve start','resolve'),(r'resolve done','resolved'),(r'^[0-9a-f]{64}$','kit_verified'),(r'stage \w+ on','staging'),
                   (r'frames f(\d+) verified','frames'),(r'init mirror','init_mirror'),(r'stage \w+ done','staged'),(r'^\{"v"','gpu_guard_pass')]:
    if re.search(pat,jtxt,re.M):stage=name
  m=re.findall(r'frames (f\d+) verified',jtxt);info['frames']=m[-1] if m else None
  errs=[l for l in jtxt.splitlines() if re.search(r'Traceback|Error|REFUS|\bE\d\d\b|Killed|CANCEL|DUE TO|oom',l) and 'gpu0' not in l]
  if errs:flags.append('JOUT_ERR');info['jout_err']=errs[-3:]
  ot=sec('OTAR')[1]
  oterr=[l for l in ot.splitlines() if re.search(r'Traceback|Error|REFUS|Missing|\bE\d\d\b',l)]
  if oterr:flags.append('OTAR_ERR');info['otar_err']=[x[:200] for x in oterr[-2:]]
  logs={l.split()[1]:(int(l.split()[2]),int(l.split()[3])) for l in re.findall(r'^@@LOG .*$',raw,re.M) if len(l.split())>=4}
  if logs.get('q.log',(-1,))[0]>=0:stage='admission'
  qres=sec('QRES')[0]
  if qres:
    info['qres']=qres[:300]
    try:q=json.loads(qres);stage='admitted' if q.get('status')=='ADMIT' else 'admission_'+str(q.get('status'))
    except Exception:pass
    if 'ADMIT' not in qres:flags.append('NOT_ADMIT')
  if logs.get('v.json',(-1,))[0]>=0:stage='v_json_written'
  if logs.get('t.log',(-1,))[0]>=0:stage='training_start'
  for f in ('q.log','rooms.log','h.log','t.log'):
    e=re.search(r'^@@ERRS '+re.escape(f)+r' (\d+)',raw,re.M)
    if e and int(e.group(1))>S.get('errs_'+f,0):
      flags.append('LOGERR_'+f);S['errs_'+f]=int(e.group(1));info['err_'+f]=sec('ERRS')[1].strip().splitlines()[-2:]
  srun=re.search(r'^@@SRUN rc=(\d+)',raw,re.M)
  if state=='RUNNING':
    if not srun or srun.group(1)!='0':S['srun_bad']=S.get('srun_bad',0)+1
    else:S['srun_bad']=0
    if S.get('srun_bad',0)>=2:flags.append('SRUN_FAIL')
  # metrics
  steps=[json.loads(l[7:]) for l in re.findall(r'^@@STEP .*$',raw,re.M)]
  mp=sec('MP')[0]; 
  if mp and mp!='-':S['mp']=mp
  seen=S.setdefault('seen',{}); new=[]
  for r in steps:
    k=str(r['step'])
    if k not in seen:seen[k]=1;new.append(r)
    with open(os.path.join(D,'steps.jsonl'),'a') as f:
      if r in new:f.write(json.dumps(r)+'\n')
  if steps:stage='training'
  allsteps=[json.loads(l) for l in open(os.path.join(D,'steps.jsonl'))] if os.path.exists(os.path.join(D,'steps.jsonl')) else []
  allsteps.sort(key=lambda r:r['step'])
  def bad(x):return isinstance(x,float) and not math.isfinite(x)
  for r in new:
    nfr=[k['rank'] for k in r['ranks'] if k.get('nf') or any(bad(v) for v in (k.get('sm') or {}).values()) or bad(k.get('csum'))]
    r['_nfr']=nfr
    if nfr:flags.append('NONFINITE step %s ranks %s'%(r['step'],nfr))
    if r.get('top_nf'):warn.append('nonfinite outside ranks step %s'%r['step'])
    if sum(k.get('skip',0) for k in r['ranks']):warn.append('skipped microsteps step %s'%r['step'])
  # stop bar: every rank non-finite on two consecutive steps
  nfall=[r['step'] for r in allsteps if r['ranks'] and all(k.get('nf') or any(bad(v) for v in (k.get('sm') or {}).values()) for k in r['ranks'])]
  stop=any(b-a==1 for a,b in zip(nfall,nfall[1:]))
  # loss bars per stream (four-rank mean)
  def mean(r,s):
    v=[k['sm'][s] for k in r['ranks'] if k.get('sm') and isinstance(k['sm'].get(s),(int,float)) and math.isfinite(k['sm'][s])]
    return sum(v)/len(v) if v else None
  for s in BASE:
    thr=BASE[s]+max(0.5*BASE[s],6*1.4826*MAD[s]); seq=[mean(r,s) for r in allsteps[-3:]]
    if len(seq)==3 and all(x is not None and x>3*BASE[s] for x in seq):flags.append('LOSS3X_%s'%s)
    elif len(seq)>=2 and all(x is not None and x>thr for x in seq[-2:]):warn.append('loss_high_%s %.4f>%.4f'%(s,seq[-1],thr))
  walls=[max(k['wall'] for k in r['ranks'] if k.get('wall') is not None) for r in allsteps if r['ranks']]
  if allsteps:
    last=allsteps[-1]; info['step']=last['step']; info['wall']=round(walls[-1]); info['streams']={s:(round(mean(last,s),5) if mean(last,s) is not None else None) for s in ('pose','vqa','routing','pointing')}
    info['csum']=[round(k['csum'],5) if isinstance(k.get('csum'),float) else k.get('csum') for k in last['ranks']]
    slow=[r['step'] for r,w in zip(allsteps,walls) if w>300 and r['step']!=allsteps[0]['step'] and not any((k.get('ck') or 0)>0 or (k.get('ex') or 0)>0 for k in r['ranks'])]
    if slow and slow[-1]==last['step']:flags.append('SLOW step %s %ss'%(slow[-1],round(walls[-1])))
    med=st.median(walls[1:] or walls); info['med_wall']=round(med)
    if left is not None and med:
      tgt=next((t for t in (100,200,400,600,800,1000) if t>last['step']),None)
      if tgt:
        eta=(tgt-last['step'])*med+300; info['eta_%d_min'%tgt]=round(eta/60); info['left_min']=round(left/60)
        if tgt<200:info['eta_200_min']=round(((200-last['step'])*med+300)/60)
        eff=left-3600  # trainer self-stops at limit - 3600 s
        stop_step=int(open(os.path.join(D,'stop_step')).read()) if os.path.exists(os.path.join(D,'stop_step')) else 400
        for t2 in sorted(x for x in ({tgt,200} if last['step']<200 else {tgt}) if x<=stop_step):
          e2=(t2-last['step'])*med+300
          if e2+1800>eff:flags.append('TIME: step %d needs ~%d min, %d min before self-stop'%(t2,e2/60,eff/60))
  # stall: progress signature
  cg=re.findall(r'^@@CG (\S+) max=(\S+) cur=(\d+) (.*?)cpu_usec=(\d+)',raw,re.M)
  cg=[c for c in cg if '/step_' not in c[0]] or cg[-1:]
  cpu=int(cg[0][4]) if cg else None
  if cg:
    st_=dict(re.findall(r'(anon|file|shmem) (\d+)',cg[0][3])); mx=cg[0][1]; used=int(st_.get('anon',0))+int(st_.get('shmem',0))
    info['mem_anon_shmem_G']=round(used/2**30,1)
    if mx.isdigit():
      info['mem_max_G']=round(int(mx)/2**30)
      if used>0.9*int(mx):flags.append('MEM>90%')
  tdf=sec('TMPDF')[0]
  if tdf and tdf.isdigit():
    info['tmp_free_G']=int(tdf)
    if int(tdf)<300:flags.append('NODE_TMP<300G')
  pc=sec('PCOUNT')[0]
  sig=json.loads(json.dumps([jsz,sorted(logs.items()),pc,len(seen)]))
  if state=='RUNNING':
    prev=S.get('sig');pcpu=S.get('cpu');pt=S.get('t')
    busy=(cpu is not None and pcpu is not None and pt and now>pt and (cpu-pcpu)/1e6/(now-pt)>=0.5)
    if prev==sig and not busy and not S.get('still'):S['still']=now
    elif prev!=sig:S['still']=None
    if prev==sig and not busy and S.get('still') and now-S['still']>=600:flags.append('STALL %d min'%((now-S['still'])/60))
    if prev==sig and busy:S['still']=None
    if cpu is not None and pcpu is not None and pt and now>pt:info['cores']=round((cpu-pcpu)/1e6/(now-pt),1)
    if stage=='training' and allsteps:
      lt=S.get('last_step_t'); 
      if new:S['last_step_t']=now
      elif lt and now-lt>max(3*info.get('med_wall',150),900):flags.append('NO_NEW_STEP %d min'%((now-lt)/60))
    gpu=[l.split(',') for l in sec('GPU')[1].splitlines() if l.count(',')>=3]
    if gpu:
      info['gpu_util']=[int(g[1]) for g in gpu if g[1].strip().isdigit()]; info['gpu_mem_G']=[round(int(g[2])/1024) for g in gpu if g[2].strip().isdigit()]
      if stage=='training' and info['gpu_util'] and max(info['gpu_util'])==0:
        S['gpu0']=S.get('gpu0',0)+1
        if S['gpu0']>=2:flags.append('GPU_IDLE')
      else:S['gpu0']=0
  S['sig']=sig;S['cpu']=cpu;S['t']=now
  info['stage']=stage; S['stage']=stage
  live=sec('LIVE')[1]+sec('LSTATE')[1]; gd=sorted(set(re.findall(r'gcs_(m\w+)\.done',live))); info['gcs_done']=gd
  if gd!=S.get('gcs_done',[]):warn.append('NEW_GCS_DONE '+','.join(gd));S['gcs_done']=gd
  if re.search(r'gcs_m\w+\.json',live):warn.append('gcs_json_present(export not uploaded?)')
  if re.search(r'WAITING_REVIEW',live):
    S.setdefault('wr_since',now); info['waiting_review_min']=round((now-S['wr_since'])/60); warn.append('WAITING_REVIEW')
    if 'review.json' not in sec('NR')[1] and now-S['wr_since']>1800:flags.append('NO_REVIEW_30MIN')
  if logs.get('q.log',(-1,))[0]>=0:
    S.setdefault('q_start',now); info['prep_min']=round((now-S['q_start'])/60); info['prep_pct_vs141']=round(100*(now-S['q_start'])/60/141)
  nck=sec('NCK')[1].strip()
  if nck:info['n_ck']=nck.splitlines()[-2:]
  ck=sec('CK')[1].strip().splitlines(); info['ck']=ck[-3:]
  if ck and ck!=S.get('ck'):S['ck_new']=ck;warn.append('NEW_CK_MARKER')
  S['ck']=ck
  # post-preparation refusal points (ORCH 0924Z item 3): train start after review, first step, first checkpoint, each export
  if state=='RUNNING':
    if 'review.json' in sec('NR')[1] and logs.get('t.log',(-1,))[0]<0:
      S.setdefault('rv_since',now); m=(now-S['rv_since'])/60; info['review_to_train_min']=round(m)
      if m>=20:flags.append('NO_TRAIN_START %d min after review.json'%m)
    if stage=='training_start':
      S.setdefault('ts_since',now); m=(now-S['ts_since'])/60; info['train_start_min']=round(m)
      if m>=45:flags.append('NO_FIRST_STEP %d min after t.log'%m)
    if not allsteps:S['ck_pre']=[c for c in ck if 'checkpoint_' in c]
    else:
      S.setdefault('step1_t',now)
      newck=[c for c in ck if 'checkpoint_' in c and c not in S.get('ck_pre',[])]
      if newck:S['first_ck']=S.get('first_ck') or newck[0]
      elif not S.get('first_ck') and now-S['step1_t']>=1500:flags.append('NO_FIRST_CK %d min after step 1'%((now-S['step1_t'])/60))
      last_s=allsteps[-1]['step']; due=S.setdefault('ex_due',{})
      for t in (100,200,400,600,800,1000):
        if last_s>t and 'm%d'%t not in gd:
          due.setdefault(str(t),now)
          if now-due[str(t)]>=2700:flags.append('NO_EXPORT_m%d %d min after step %d'%(t,(now-due[str(t)])/60,t+1))
  # ORCH RULING 2232Z item 3: an export exists (m<t>/artifact.json) and no upload receipt 10 min later
  rc_h,_=sec('RCPT'); exps=sorted(set(re.findall(r'\b(m\d+)/artifact\.json',sec('CK')[1])))
  if exps and rc_h is not None and rc_h.isdigit():
    S.setdefault('exp1_t',now); info['receipts']=int(rc_h); info['exports_seen']=exps
    if int(rc_h)==0 and now-S['exp1_t']>=600:flags.append('NO_RECEIPT_10MIN after export %s'%exps[0])
  if stop:flags.append('STOP_BAR')
else:
  info['adv_jobs']=[q[0]+':'+q[1]+':'+q[3] for q in adv]
json.dump(S,open(SP,'w'))
line='%s job=%s %s %s'%(now_s[11:20],J,json.dumps(info,separators=(',',':'))[:900],('WARN '+'; '.join(warn)) if warn else '')
print(line+(' FLAG '+' | '.join(flags) if flags else ''))
sys.exit(4 if any(f=='STOP_BAR' for f in flags) else (2 if flags else 0))
