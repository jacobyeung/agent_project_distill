export TZ=UTC
Q=/tmp/q_22c714e1_174246
echo "host $(hostname -s) $(date -u +%FT%TZ)"
/usr/bin/python3 -B -I - <<'PY'
import json,os,base64,hashlib,glob
Q='/tmp/q_22c714e1_174246'
X='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b'
P='/project/community/jjyeung/c7d31ddd'
def load(p):
    v=json.loads(open(p).read())
    if isinstance(v,dict) and v.get('encoding')=='base64-json':
        v=json.loads(base64.b64decode(v['payload']))
    return v
inner=None
for d in os.listdir('/proc'):
    if not d.isdigit(): continue
    try:
        if os.stat('/proc/'+d).st_uid!=os.getuid(): continue
        a=[x.decode('utf-8','replace') for x in open('/proc/%s/cmdline'%d,'rb').read().split(b'\0') if x]
    except Exception: continue
    if a and '--ro-bind' not in a and 'python' in os.path.basename(a[0]) and any(x.endswith('/b/rv.py') for x in a) and os.path.isdir('/proc/%s/root%s'%(d,X)): inner=int(d)
print('inner pid',inner);R='/proc/%d/root'%inner
def ex(p):
    try:
        s=os.stat(R+p);return 'DIR' if os.path.isdir(R+p) else 'FILE %d'%s.st_size
    except Exception as x: return 'ABSENT'
def sh(p):
    h=hashlib.sha256();h.update(open(p,'rb').read());return h.hexdigest()
cfg=load(Q+'/v.json');req=load(Q+'/r.json');rt=cfg['r1_training']
m={**(req.get('_paths') or {}),**rt['persisted_files']}
print('== cfg output',cfg.get('output'),'| preparation',json.dumps(cfg.get('preparation'))[:260],ex(cfg['preparation']['path']) if cfg.get('preparation') else '')
print('   cfg code',json.dumps(cfg.get('code'))[:260]);print('   cfg keys',sorted(cfg)[:60])
print('   review',json.dumps(rt.get('review'))[:200],'| handover_mapping',json.dumps(rt.get('handover_mapping'))[:400])
def pins(v,path=''):
    if isinstance(v,dict):
        if set(v)=={'path','sha256'} and isinstance(v['path'],str): yield path,v
        else:
            for k,x in v.items(): yield from pins(x,path+'/'+str(k))
    elif isinstance(v,list):
        for i,x in enumerate(v): yield from pins(x,path+'/'+str(i))
def table(name,obj,limit=40):
    rows=list(pins(obj));bad=[(k,p) for k,p in rows if ex(p['path'])=='ABSENT']
    print('== %s: %d pins, raw path absent in the live sandbox for %d'%(name,len(rows),len(bad)))
    for k,p in bad[:limit]:
        rel=m.get(p['sha256']);print('   %-46s raw %s | relocated %s [%s]'%(k[-46:],p['path'].replace(X,'$X')[:100],(rel or 'NONE')[:90],ex(rel) if rel else '-'))
table('cfg (v.json)',{k:v for k,v in cfg.items()})
cands=sorted(glob.glob('/tmp/a15_rh_174246/run_*/w/top/p/pr.json'))+[Q+'/p/pr.json']
pr=None
for c in cands:
    if os.path.isfile(c): pr=c
print('== receipt candidates',cands,'using',pr)
if pr:
    rc=load(pr);print('   receipt keys',sorted(rc)[:70])
    print('   init_artifact',json.dumps(rc.get('init_artifact'))[:400])
    for k in ('depth_init','align','model'): print('  ',k,json.dumps(rc.get(k))[:300])
    go=rc.get('geometry_online') or {};print('   geometry_online.encoder',json.dumps(go.get('encoder'))[:500])
    if go.get('encoder'):
        for k in ('config','weights'):
            p=go['encoder'][k];print('   gx %s raw %s [%s] relocated %s'%(k,p['path'][:140],ex(p['path']),m.get(p['sha256'])))
    if 'mdg' in rc: print('   mdg',json.dumps(rc['mdg'])[:300])
    table('receipt (rehearsal stand-in pr.json)',rc)
    mroot=load(R+m.get(rc['model']['sha256'],rc['model']['path'])) if isinstance(rc.get('model'),dict) and 'sha256' in rc['model'] else None
    if mroot: print('   base manifest root',mroot.get('root'),ex(mroot.get('root','/nonexistent')))
print('== mirror vs relocated artifact')
ia=cfg['init_artifact']['artifact'];mdir=Q+'/s/c7d31ddd/init/1d6eeb28f51688c4'
a1=load(mdir+'/artifact.json');a2=load(R+ia['path'])
print('   mirror artifact sha256',sh(mdir+'/artifact.json')[:16],'step',a1.get('step'),'config',str(a1.get('config_sha256'))[:12],'heads',a1['heads']['sha256'][:12],a1['heads']['path'].replace(X,'$X'),'fw',a1['full_weights']['sha256'][:12],a1['full_weights']['path'].replace(X,'$X'))
print('   config artifact sha256',sh(R+ia['path'])[:16],'step',a2.get('step'),'config',str(a2.get('config_sha256'))[:12],'heads',a2['heads']['sha256'][:12],a2['heads']['path'].replace(X,'$X'),'fw',a2['full_weights']['sha256'][:12],a2['full_weights']['path'].replace(X,'$X'))
print('   differing top-level keys',[k for k in sorted(set(a1)|set(a2)) if a1.get(k)!=a2.get(k)][:30])
try: print('   0.json init',json.dumps(load(Q+'/h/k/0.json').get('init'))[:300])
except Exception as x: print('0.json',repr(x))
print('== filesystems and link partners')
for p in (Q+'/rp',Q+'/p/q/w',Q+'/p/q/u',Q+'/s/c7d31ddd/init/1d6eeb28f51688c4/full_weights'):
    s=os.stat(p);print('   %s dev %d'%(p,s.st_dev))
for a,b in ((Q+'/p/q/w/full_weights.json',mdir+'/full_weights/full_weights.json'),(Q+'/p/q/w/model-00005-of-00005.safetensors',mdir+'/full_weights/model-00005-of-00005.safetensors'),(Q+'/p/q/u/'+a2['heads']['sha256'],mdir+'/heads.pt')):
    try:
        sa,sb=os.lstat(a),os.lstat(b);print('   %s ino %d nlink %d %s | mirror ino %d nlink %d'%(a.replace(Q,'$Q')[-60:],sa.st_ino,sa.st_nlink,'LINK->'+os.readlink(a) if os.path.islink(a) else 'regular',sb.st_ino,sb.st_nlink))
    except Exception as x: print('   ',a,repr(x))
print('   p/q entries',sorted(os.listdir(Q+'/p/q'))[:30]);print('   p entries',sorted(os.listdir(Q+'/p'))[:30]);print('   top entries',sorted(os.listdir(Q))[:60])
print('   symlink targets visible in sandbox: /tmp/q_22c714e1/p/q/w',ex('/tmp/q_22c714e1/p/q/w'),'heads',ex('/tmp/q_22c714e1/p/q/u/'+a2['heads']['sha256']))
PY
echo inner_rc=$?
