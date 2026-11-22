export TZ=UTC
Q=/tmp/q_22c714e1_174246
echo "host $(hostname -s) $(date -u +%FT%TZ)"
/usr/bin/python3 -B -I - <<'PY'
import json,os,base64
Q='/tmp/q_22c714e1_174246'
X='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b'
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
cfg=load(Q+'/v.json');req=load(Q+'/r.json');rt=cfg['r1_training']
m={**(req.get('_paths') or {}),**rt['persisted_files']}
def pins(v,path=''):
    if isinstance(v,dict):
        if set(v)=={'path','sha256'} and isinstance(v['path'],str): yield path,v
        else:
            for k,x in v.items(): yield from pins(x,path+'/'+str(k))
    elif isinstance(v,list):
        for i,x in enumerate(v): yield from pins(x,path+'/'+str(i))
for name,pin in (('init_artifact.artifact',cfg['init_artifact']['artifact']),('depth_init',cfg.get('depth_init'))):
    if not pin: print('==',name,'none');continue
    p=m.get(pin['sha256'],pin['path']);a=load(R+p)
    print('== %s at %s schema %s: embedded pins'%(name,p,a.get('schema')))
    for k,q in pins(a):
        rel=m.get(q['sha256']);print('   %-28s raw %s [%s] | relocated %s [%s] in persisted_files=%s in _paths=%s'%(k,q['path'][:150],ex(q['path']),(rel or 'NONE')[:110],ex(rel) if rel else '-',q['sha256'] in rt['persisted_files'],q['sha256'] in (req.get('_paths') or {})))
print('== cfg depth_init',json.dumps(cfg.get('depth_init'))[:300],'| cfg init',json.dumps(cfg.get('init'))[:300])
print('== rp writable by this user (access check only):',os.access(Q+'/rp',os.W_OK),'mode',oct(os.stat(Q+'/rp').st_mode))
for d in ('/project/community/jjyeung/okh7/h_6ed2c7aa','/project/community/jjyeung/okh7/h_6ed2c7aa/m400'):
    try: print('== ls',d,sorted(os.listdir(d))[:30])
    except Exception as x: print('== ls',d,repr(x))
w=Q+'/p/q/w'
print('== p/q/w entries',[(n,'link->'+os.readlink(w+'/'+n) if os.path.islink(w+'/'+n) else os.stat(w+'/'+n).st_nlink) for n in sorted(os.listdir(w))])
hm=rt.get('handover_mapping')
if hm:
    try:
        h=load(R+hm['path']);print('== handover_mapping keys',sorted(h)[:20],json.dumps(h)[:700])
    except Exception as x: print('mapping',repr(x))
PY
echo inner_rc=$?
