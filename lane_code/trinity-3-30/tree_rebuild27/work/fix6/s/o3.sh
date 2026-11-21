export TZ=UTC; date -u +%TZ
timeout 200 srun --overlap --jobid 174134 -N1 -n1 python3 -I -B - <<'PYEOF'
import json, hashlib, os, sys, glob, base64
OUT='/tmp/q_22c714e1_174134'; IN='/tmp/q_22c714e1'
def m(p):
    p=str(p)
    return OUT+p[len(IN):] if (p==IN or p.startswith(IN+'/')) else p
def L(path):
    v=json.load(open(m(path)))
    if isinstance(v,dict) and v.get('encoding')=='base64-json': v=json.loads(base64.b64decode(v['payload']))
    return v
def ispin(v): return isinstance(v,dict) and set(v)=={'path','sha256'}
Q=OUT+'/p/q'
R=json.load(open(Q+'/RESULT.json')); RELOC={e['sha256']:e['path'] for e in R['staged']}
cfg=L(Q+'/c.json')
for k,v in cfg.get('r1_training',{}).get('persisted_files',{}).items():
    if isinstance(v,str): RELOC.setdefault(k,v)
def res(pin): return m(RELOC.get(pin['sha256'],pin['path']))
print('== A. the N stream receipt staged for the third stream (full bytes)')
p=res(cfg['r1_training']['store_parameter']); print(p, os.path.getsize(p)); print(open(p).read())
print('== B. the receipt made by the augment step (full)'); print(open(Q+'/twins/receipt.json').read()[:3000])
print('== C. P side: P config streams and each receipt division pin')
try:
    pr=cfg['r1_training']['p_run']; print('p_run keys',sorted(pr))
    pc=L(res(pr['config'])); print('P config streams:')
    for k,v in pc['streams'].items():
        print('  ',k,json.dumps(v))
        try:
            r=L(res(v)); print('      schema',r.get('schema'),'stream',r.get('stream'),'count',r.get('count'),'heldout_overlap',r.get('heldout_overlap'),'division',json.dumps(r.get('division')),'source_receipt',json.dumps(r.get('source_receipt'))[:300])
            sr=r.get('source_receipt')
            if ispin(sr):
                try:
                    r2=L(res(sr)); print('      source_receipt: schema',r2.get('schema'),'count',r2.get('count'),'division',json.dumps(r2.get('division')),'database',json.dumps(r2.get('database')))
                except Exception as e: print('      source_receipt load failed',repr(e))
        except Exception as e: print('      load failed',repr(e))
    print('P scene_division',json.dumps(pc.get('scene_division')))
except Exception as e: print('P side failed',repr(e))
print('N scene_division',json.dumps(cfg.get('scene_division')))
print('== D. pins by sha256 with more than one path string, over all staged JSON under 40 MB plus the files the run wrote')
files=[]
for e in R['staged']:
    files.append(m(e['path']))
for pat in ('/c.json','/m.json','/v.json','/e.json','/n.json','/ss.json','/twins/*.json','/p/prepare_*/*.json','/p/prepare_*/*/receipt.json','/p/prepare_*/routing/materialization.json','/p/request.json','/sc/*.json','/sc/*/*.json','/sc/*/*/*.json','/sc/*/*/*/*.json'):
    files+=sorted(glob.glob(Q+pat))
seen={}; kinds={}; nj=0; skipped=0
def walk(v,f):
    if ispin(v):
        seen.setdefault(v['sha256'],{}).setdefault(v['path'],set()).add(f)
    elif isinstance(v,dict):
        for x in v.values(): walk(x,f)
    elif isinstance(v,list):
        for x in v: walk(x,f)
for f in dict.fromkeys(files):
    try:
        if not os.path.isfile(f) or os.path.getsize(f)>(40<<20): skipped+=1; continue
        with open(f,'rb') as h: b=h.read(1)
        if b not in (b'{',b'['): continue
        v=L(f); nj+=1
        if isinstance(v,dict): kinds[f]=str(v.get('schema'))
        walk(v,f)
    except Exception as e: pass
print('json files read',nj,'skipped(big/missing)',skipped,'distinct pinned sha',len(seen))
def norm(p):
    # the kit's own localisation is not a second authoring path
    return p
multi={s:d for s,d in seen.items() if len(d)>1}
print('sha with >1 path string:',len(multi))
def tag(f):
    b=os.path.basename(f); return (b[:10] if len(b)==64 else f.replace(Q,'q'))+'['+kinds.get(f,'?')+']'
for s,d in sorted(multi.items()):
    target=m(RELOC.get(s,'')); kind='?'
    try:
        if target and os.path.isfile(target) and os.path.getsize(target)<(40<<20):
            with open(target,'rb') as h: b=h.read(1)
            if b in (b'{',b'['):
                t=L(target); kind=str(t.get('schema')) if isinstance(t,dict) else 'json-list'
            else: kind='binary'
        elif target and os.path.isfile(target): kind='big %d'%os.path.getsize(target)
        else: kind='not-staged'
    except Exception as e: kind='err'
    print(' sha',s[:12],'target',kind)
    for pth,fs in sorted(d.items()):
        print('     ',pth,' <- in',len(fs),'file(s):',', '.join(sorted(tag(f) for f in fs))[:400])
print('DONE')
PYEOF
echo srun_rc=$?
