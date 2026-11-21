export TZ=UTC; date -u +%TZ
timeout 200 srun --overlap --jobid 174134 -N1 -n1 python3 -I -B - <<'PYEOF'
import sys; print('python',sys.version.split()[0])
import json, hashlib, os, sys, glob, base64
OUT='/tmp/q_22c714e1_174134'; IN='/tmp/q_22c714e1'
def m(p):
    p=str(p)
    return OUT+p[len(IN):] if (p==IN or p.startswith(IN+'/')) else p
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def L(path):
    v=json.load(open(m(path)))
    if isinstance(v,dict) and v.get('encoding')=='base64-json':
        v=json.loads(base64.b64decode(v['payload']))
    return v
RELOC={}
def res(pin):
    p=RELOC.get(pin['sha256'],pin['path'])
    return m(p)
def LP(pin,check=True):
    p=res(pin)
    if check and os.path.getsize(p)<(200<<20):
        s=sha(p)
        if s!=pin['sha256']: print('   !! sha differs for',p,s[:12],'pin',pin['sha256'][:12])
    return L(p)
def ispin(v): return isinstance(v,dict) and set(v)=={'path','sha256'}
def short(v,n=260):
    s=json.dumps(v,sort_keys=True) if not isinstance(v,str) else v
    return s if len(s)<=n else s[:n]+'...(%d chars)'%len(s)
def summ(d,name):
    print('  --',name,'keys:',sorted(d))
    for k in sorted(d):
        v=d[k]
        if isinstance(v,(str,int,float,bool)) or v is None or ispin(v): print('     %s = %s'%(k,short(v)))
        elif isinstance(v,dict): print('     %s : dict keys %s'%(k,short(sorted(v),200)))
        elif isinstance(v,list): print('     %s : list len %d'%(k,len(v)))
Q=OUT+'/p/q'
try:
    R=json.load(open(Q+'/RESULT.json'))
    for e in R.get('staged',[]): RELOC[e['sha256']]=e['path']
    print('RESULT keys',sorted(R),'staged',len(R.get('staged',[])))
except Exception as e: print('RESULT read failed',repr(e))
print('== p/q/p listing')
for root in sorted(glob.glob(Q+'/p/*')):
    print(root, 'dir' if os.path.isdir(root) else os.path.getsize(root))
    if os.path.isdir(root):
        for a in sorted(os.listdir(root)):
            pa=os.path.join(root,a)
            if os.path.isdir(pa):
                print('   ',a+'/',[ (b,os.path.getsize(os.path.join(pa,b))) if os.path.isfile(os.path.join(pa,b)) else b+'/' for b in sorted(os.listdir(pa))][:40])
            else: print('   ',a,os.path.getsize(pa))
req=json.load(open(Q+'/p/request.json')); print('== request',short(req,900))
cfg=LP(req['config'])
pf=cfg.get('r1_training',{}).get('persisted_files',{})
print('== cfg keys',sorted(cfg))
print('persisted_files type',type(pf).__name__,len(pf))
if isinstance(pf,dict):
    for k,v in pf.items():
        if isinstance(v,str): RELOC.setdefault(k,v)
print('training_mode',cfg.get('training_mode'),'world',cfg.get('world_size'),'s1_routing' in cfg,'r1_training keys',sorted(cfg.get('r1_training',{})))
print('== cfg streams (before)')
for k,v in cfg['streams'].items(): print('  ',k,short(v))
before={}
for k,v in cfg['streams'].items():
    try:
        before[k]=LP(v); summ(before[k],'before '+k)
    except Exception as e: print('  before',k,'load failed',repr(e))
prep=sorted(glob.glob(Q+'/p/prepare_*'))[0]
print('== prepare dir',prep)
new={}
for sub in sorted(os.listdir(prep)):
    f=os.path.join(prep,sub,'receipt.json')
    if os.path.isfile(f):
        new[sub]=json.load(open(f)); summ(new[sub],'rebuilt '+sub+' sha '+sha(f)[:16])
for f in sorted(glob.glob(prep+'/*.json')):
    try: summ(json.load(open(f)),os.path.basename(f))
    except Exception as e: print(f,repr(e))
# the run's reference division
P=before.get('pose',{})
print('== reference side: schema',P.get('schema'))
ref=None
if P.get('schema')=='c1-pose-mix-v1':
    ref=P.get('division'); print('   spec-level division pin',short(ref))
    for i,s in enumerate(P.get('sources',[])):
        print('   source',i,'kind',s.get('kind'),'keys',sorted(s))
        if 'receipt' in s:
            try:
                r=LP(s['receipt']); print('      schema',r.get('schema'),'count',r.get('count'),'inputs.division',short(r.get('inputs',{}).get('division')))
            except Exception as e: print('      load failed',repr(e))
else:
    ref=P.get('inputs',{}).get('division'); print('   inputs.division',short(ref))
def div(pin,tag):
    try:
        d=LP(pin)
    except Exception as e:
        print('   ',tag,'LOAD FAILED',repr(e),short(pin)); return None
    print('   ',tag,short(pin)); print('       resolved',res(pin),'schema',d.get('schema'),'training_only',d.get('training_only'),'train',len(d.get('train_scenes',[])),'heldout',len(d.get('heldout_scenes',[])),'parent_division',short(d.get('parent_division')),'keys',sorted(d))
    return d
def chain(pin,tag):
    out=[];cur=pin
    for i in range(6):
        if not ispin(cur): break
        d=div(cur,'%s[%d]'%(tag,i))
        if d is None: break
        out.append((cur,d)); cur=d.get('parent_division')
    return out
print('== reference division chain'); refchain=chain(ref,'ref') if ispin(ref) else []
def admits(sd,pd):
    # same logic as the tree check, verbose
    if sd==pd: return True,'equal pins'
    why=[]
    if ispin(sd) and ispin(pd) and sd['sha256']==pd['sha256']: why.append('SAME SHA256, PATH DIFFERS: %s vs %s'%(sd['path'],pd['path']))
    # ancestor walk from pd up to sd
    cur=pd
    try:
        c=LP(cur,False)
        for i in range(4):
            if c.get('schema')!='diagnostic-whole-scene-division-v1' or c.get('training_only') is not True:
                why.append('walk[%d]: child not a training-only whole-scene division (schema %s training_only %s)'%(i,c.get('schema'),c.get('training_only'))); break
            pp=c.get('parent_division')
            if not ispin(pp): why.append('walk[%d]: no parent pin'%i); break
            p=LP(pp,False)
            if p.get('schema')!='diagnostic-whole-scene-division-v1' or p.get('training_only') is not True:
                why.append('walk[%d]: parent not a training-only whole-scene division'%i); break
            ok=set(p['train_scenes'])<=set(c['train_scenes']) and set(p['heldout_scenes'])<=set(c['heldout_scenes'])
            if not ok: why.append('walk[%d]: parent scenes not kept (train missing %d, heldout missing %d)'%(i,len(set(p['train_scenes'])-set(c['train_scenes'])),len(set(p['heldout_scenes'])-set(c['heldout_scenes'])))); break
            if pp==sd: return True,'ancestor at depth %d'%(i+1)
            if pp['sha256']==sd['sha256']: why.append('walk[%d]: parent pin has SAME SHA256 as stream division but PATH DIFFERS: %s vs %s'%(i,pp['path'],sd['path']))
            cur,c=pp,p
    except Exception as e: why.append('walk error '+repr(e))
    try:
        ch=LP(sd,False)
        if ch.get('parent_division')!=pd:
            why.append('child rule: stream division parent_division %s != reference'%short(ch.get('parent_division')))
            if ispin(ch.get('parent_division')) and ch['parent_division']['sha256']==pd['sha256']: why.append('child rule: SAME SHA256, PATH DIFFERS')
        else:
            held=set(LP(pd,False)['heldout_scenes'])
            ok=held<=set(ch['heldout_scenes']) and not held&set(ch['train_scenes'])
            if ok: return True,'child with parent_division'
            why.append('child rule: heldout not contained (%d missing, %d in train)'%(len(held-set(ch['heldout_scenes'])),len(held&set(ch['train_scenes']))))
    except Exception as e: why.append('child rule error '+repr(e))
    return False,' | '.join(why)
print('== the check at line 539-541, per stream, on the receipts prepare() saw')
sel=dict(cfg['streams'])
names={'pointing':'pointing','vqa':'vqa','routing':'composed' if 'composed' in new else 'routing'}
for name in cfg['streams']:
    if name in ('pose','mdg'): continue
    r=new.get(names.get(name,name))
    src='rebuilt '+names.get(name,name)
    if r is None: r=before.get(name); src='before (no rebuilt receipt on disk)'
    if r is None: print('  ',name,'no receipt'); continue
    print('  stream',name,'from',src)
    print('     schema =',r.get('schema'),'| stream =',r.get('stream'),'| heldout_overlap =',r.get('heldout_overlap'),'| gt_masks_only =',r.get('gt_masks_only'),'| scene_role =',r.get('scene_role'),'| count =',r.get('count'))
    print('     division pin =',short(r.get('division')))
    if ispin(r.get('division')):
        chain(r['division'],'     '+name+'.division')
        if ispin(ref): print('     division_admits ->',admits(r['division'],ref))
    if src.startswith('rebuilt') and name in before and before[name].get('division')!=r.get('division'): print('     note: before-receipt division pin differs:',short(before[name].get('division')))
print('DONE')
PYEOF
echo srun_rc=$?
