"""Replay 172660's recorded per-step four-rank means (r1_ops6 mon/node_hist.txt, steps 207-600) through parse.py: a healthy run must raise no FLAG."""
import json,sys,subprocess,os
sys.path.insert(0,'/scratch/jjyeung/orch_n30/n_ops1/work/tests'); import run_tests as T
rows={}
for l in open('/scratch/jjyeung/orch_n30/r1_ops6/work/mon/node_hist.txt'):
  if ' STEP ' in l:
    s=l.split(' STEP ',1)[1]; s=s[:s.index('}')+1] if '}' in s else s.rsplit(',',1)[0]+'}'
    try:d=json.loads(s)
    except Exception:continue
    rows[d['step']]=d
ks=sorted(rows); seq=[]; t=0; hist=[]
for n in ks:
  r=rows[n]; sm={k:r.get(k,T.SM[k]) for k in T.SM}
  hist.append(T.step(n,sm=sm,wall=r['wall'],ck=65 if n%200==0 else 0)); t+=r['wall']*(n-(hist[-2]['step'] if len(hist)>1 else n-1))
  m=int(t//60); left=24*3600-3.5*3600-t
  r0=T.raw('%02d:%02d:%02dZ'%((m//60)%24,m%60,int(t%60)),steps=hist[-3:],cpu=t*8e6,left='%d:%02d:00'%(left//3600,(left%3600)//60))
  done=['m100','m200']+[x for x in ('m400','m600') if n>=int(x[1:])+4]
  r0=r0.replace('@@CK\n','@@CK\n00:00:00.0 r/checkpoint_000001\n').replace('@@ODIR','@@LIVE\n'+''.join('-rw------- 1 u g 107 00:00:00 gcs_%s.done\n'%x for x in done)+'@@ODIR')
  seq.append(r0)
d=T.W+'/tests/s_replay'; os.makedirs(d,exist_ok=True); json.dump({'job':'99'},open(d+'/state.json','w'))
for f in ('steps.jsonl',):
  if os.path.exists(d+'/'+f):os.replace(d+'/'+f,d+'/'+f+'.prev')
nflag=0
for r in seq:
  open(d+'/raw','w').write(r); p=subprocess.run([T.PY,T.W+'/parse.py',d+'/raw',d],capture_output=True,text=True)
  if 'FLAG' in p.stdout or 'WARN' in p.stdout:nflag+=1;print(p.stdout.strip()[-250:])
print('replayed',len(seq),'checks; flagged',nflag)
