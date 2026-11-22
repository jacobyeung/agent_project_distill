export TZ=UTC
Q=/tmp/q_22c714e1_174246
echo "host $(hostname -s) $(date -u +%FT%TZ)"
echo "== steps"; grep -n -E "init mirror|stage .* done" $Q/174246.steps | cut -c1-200 | tail -8; tail -n 4 $Q/174246.steps | cut -c1-200
echo "== rp (host $Q/rp)"; ls -la $Q/rp 2>&1 | head -20 | cut -c1-160
for d in rp/6ed2c7aa rp/6ed2c7aa/m400 rp/6ed2c7aa/m400/full_weights x/runs; do echo "== $d"; ls -la $Q/$d 2>&1 | head -24 | cut -c1-160; done
echo "== init mirror on host ($Q/s/c7d31ddd/init)"; ls -la $Q/s/c7d31ddd/init 2>&1 | head -12 | cut -c1-160
for d in $Q/s/c7d31ddd/init/*/; do echo "-- $d"; ls -la "$d" 2>&1 | head -12 | cut -c1-160; ls -la "$d/full_weights" 2>&1 | head -24 | cut -c1-160; done
echo "== union m400 ($Q/s/aws/u/ap/8865619b/runs/6ed2c7aa/m400)"; ls -la $Q/s/aws/u/ap/8865619b/runs/6ed2c7aa/m400 2>&1 | head -12 | cut -c1-160; ls -la $Q/s/aws/u/ap/8865619b/runs 2>&1 | head -12 | cut -c1-160
echo "== j.sh 3821326"; tr "\0" " " < /proc/3821326/cmdline 2>&1 | cut -c1-300; echo; tr "\0" "\n" < /proc/3821326/environ 2>&1 | grep -E "^(C1_INIT_LOCAL|Q_|TK_|R1_|SLURM_JOB_ID=|TMPDIR=)" | cut -c1-300
/usr/bin/python3 -B -I - <<'PY'
import json,os,base64
Q='/tmp/q_22c714e1_174246'
X='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b'
P='/project/community/jjyeung/c7d31ddd'
def load(p):
    v=json.loads(open(p).read())
    if isinstance(v,dict) and v.get('encoding')=='base64-json':
        v=json.loads(base64.b64decode(v['payload']))
    return v
me=os.getuid();procs={}
for d in os.listdir('/proc'):
    if not d.isdigit(): continue
    try:
        if os.stat('/proc/'+d).st_uid!=me: continue
        a=[x.decode('utf-8','replace') for x in open('/proc/%s/cmdline'%d,'rb').read().split(b'\0') if x]
        pp=int(open('/proc/%s/stat'%d).read().rsplit(')',1)[1].split()[1])
    except Exception: continue
    if a: procs[int(d)]=(pp,a)
print('== process tree under 3821326')
def kids(p,depth=0):
    for q,(pp,a) in sorted(procs.items()):
        if pp==p:
            print('  '*depth+'%d %s'%(q,' '.join(a)[:170] if '--ro-bind' not in a else 'BWRAP nargs=%d ... %s'%(len(a),' '.join(a[-8:])[:200])))
            kids(q,depth+1)
kids(3821326)
bw=[(p,a) for p,(pp,a) in sorted(procs.items()) if '--ro-bind' in a]
inner=None
for p,a in bw[:1]:
    print('== bwrap pid',p,'nargs',len(a));i=1;same=0;out=[]
    while i<len(a):
        o=a[i]
        if o in('--bind','--ro-bind','--dev-bind','--symlink','--setenv'):
            if o=='--ro-bind' and a[i+1]==a[i+2]: same+=1
            elif o=='--symlink': pass
            else: out.append('%s %s %s'%(o,a[i+1],a[i+2][:160]))
            i+=3
        elif o in('--tmpfs','--dir','--remount-ro','--uid','--gid','--proc'):
            out.append('%s %s'%(o,a[i+1]));i+=2
        elif o.startswith('--'): out.append(o);i+=1
        else: out.append('CMD '+' '.join(a[i:])[:300]);break
    print('identical ro-binds:',same);print('\n'.join(out))
    try:
        e=dict(x.split('=',1) for x in open('/proc/%d/environ'%p,'rb').read().decode('utf-8','replace').split('\0') if '=' in x)
        print('== bwrap environ');[print(' ',k,'=',e[k][:300]) for k in sorted(e) if k.startswith(('C1_','Q_','TK_','R1_','PYTHONPATH','TMPDIR','ANYHOST','OMP_NUM'))]
    except Exception as x: print('environ',repr(x))
cand=[p for p,(pp,a) in sorted(procs.items()) if '--ro-bind' not in a and any(x.endswith('rv.py') for x in a) and 'python' in os.path.basename(a[0])]
print('== sandboxed candidates',cand)
for p in cand:
    try:
        os.listdir('/proc/%d/root/tmp'%p);inner=p
        if os.path.isdir('/proc/%d/root%s'%(p,X)): break
    except Exception as x: print(p,repr(x))
print('inner pid',inner)
R='/proc/%d/root'%inner if inner else ''
if inner:
    print('== mountinfo of inner (filtered)')
    for line in open('/proc/%d/mountinfo'%inner):
        f=line.split()
        if any(s in f[4] for s in ('8865619b','c7d31ddd','q_22c714e1','6d00e578')) and len(f[4])<200:
            print(' ',f[3][:150],'->',f[4],f[5])
    e=dict(x.split('=',1) for x in open('/proc/%d/environ'%inner,'rb').read().decode('utf-8','replace').split('\0') if '=' in x)
    print('== inner environ: C1_INIT_LOCAL=',e.get('C1_INIT_LOCAL'),'R1_MOUNT=',e.get('R1_MOUNT'),'Q_NS=',e.get('Q_NS'))
def ex(p):
    try:
        s=os.stat(R+p);return 'FILE %d'%s.st_size if not os.path.isdir(R+p) else 'DIR'
    except Exception as x: return 'ABSENT(%s)'%type(x).__name__
def ls(p,n=20):
    try: return sorted(os.listdir(R+p))[:n]
    except Exception as x: return 'ABSENT(%s)'%type(x).__name__
print('== view through the live sandbox root' if inner else '== HOST view (no sandboxed process found)')
for p in (X+'/runs',X+'/runs/6ed2c7aa',X+'/runs/6ed2c7aa/m400',X+'/runs/6ed2c7aa/m400/full_weights',P+'/init'):
    print(' ',p,ls(p))
cfg=load(Q+'/v.json');req=load(Q+'/r.json')
ia=cfg.get('init_artifact');print('== cfg init_artifact',json.dumps(ia)[:600])
rt=cfg.get('r1_training') or {};print('== r1_training keys',sorted(rt));print('   handover_receipt',rt.get('handover_receipt'),'proof_mode',rt.get('proof_mode'),'init_policy',rt.get('init_policy'))
pf=rt.get('persisted_files') or {};rp=req.get('_paths') or {}
print('== persisted_files n=%d ; request _paths n=%d ; same=%s'%(len(pf),len(rp),pf==rp))
m={**rp,**pf}
if ia:
    sha=ia['artifact']['sha256'];print('   mirror dir',P+'/init/'+sha[:16],ls(P+'/init/'+sha[:16]),'.verified',ex(P+'/init/'+sha[:16]+'/.verified'))
    print('   raw artifact path',ia['artifact']['path'],ex(ia['artifact']['path']));print('   relocated',m.get(sha),ex(m[sha]) if sha in m else '')
try:
    pr=load(Q+'/p/pr.json');print('== receipt(pr.json) init_artifact',json.dumps(pr.get('init_artifact'))[:500]);print('   geometry_online' , json.dumps((pr.get('geometry_online') or {}).get('encoder'))[:500]);print('   model pin',json.dumps(pr.get('model'))[:300],'depth_init',json.dumps(pr.get('depth_init'))[:200])
except Exception as x: print('pr.json',repr(x))
try:
    hr=rt['handover_receipt'];hp=m.get(hr['sha256'],hr['path']);h=load((R+hp) if os.path.exists(R+hp) else hp)
    pins=h['pins'];print('== handover receipt',hp,'schema',h.get('schema'),'step',h.get('step'),'pins',len(pins))
    for k in sorted(pins):
        pin=pins[k];rel=m.get(pin['sha256'])
        if k.startswith(('checkpoint/','stream/','indices/')) and ex(pin['path']).startswith(('FILE','DIR'))==False and rel is None: continue
        print('  %-34s raw %s [%s] | relocated %s [%s]'%(k,pin['path'].replace(X,'$X')[:110],ex(pin['path']),(rel or '-').replace(X,'$X')[:110],ex(rel) if rel else '-'))
    art=load(R+m.get(pins['artifact']['sha256'],pins['artifact']['path']))
    print('== artifact.json heads',json.dumps(art.get('heads'))[:300]);print('   full_weights',json.dumps(art.get('full_weights'))[:300])
    fw=art['full_weights']['path'];d=os.path.dirname(fw);print('   RAW dir (ranks 1-3 read this)',d,ls(d));print('   RAW heads',art['heads']['path'],ex(art['heads']['path']))
    rd=os.path.dirname(m.get(art['full_weights']['sha256'],fw));print('   RELOCATED dir (rank 0 reads this)',rd,ls(rd))
except Exception as x:
    import traceback;traceback.print_exc()
try:
    q=load(Q+'/p/q/RESULT.json');print('== RESULT.json keys',sorted(q)[:30],'status',q.get('status'),'init_milestone',q.get('init_milestone'))
    for k in ('absent','unread'): print('  ',k,json.dumps(q.get(k))[:500])
except Exception as x: print('RESULT',repr(x))
PY
echo inner_rc=$?
