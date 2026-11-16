import sys, json, io, tarfile, hashlib, tempfile, copy, uuid
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,'/scratch/jjyeung/orch_n30/review_d0r2/cur/tests')
sys.path.insert(0,'/scratch/jjyeung/orch_n30/review_d0r2/cur/kit/launcher')
import orchard_launcher as L
import offline_guard
import export_stage as E
def t(name, fn, expect_raise):
    try: r=fn(); out='ok '+str(r)[:90]; raised=False
    except Exception as e: out='RAISE '+type(e).__name__+': '+str(e)[:90]; raised=True
    print(('OK ' if raised==expect_raise else 'BAD'),'|',name,'|',out)
sha='a'*64
good=lambda run,step: f'q8/8865619b/{run}_m{step}.tar 21583032320 {sha}\n'.encode()
real=open('/scratch/jjyeung/orch_n30/review_d0r2/cur/evidence/DONE_SAMPLES.txt','rb').read().split(b'\n')[4]+b'\n'
print('real sample line:', real)
t('real 469ddece_m1 uploader line, run 469ddece step 1', lambda: E.parse_done(real,'469ddece',1), False)
t('real line read as 359fcc3c step 1', lambda: E.parse_done(real,'359fcc3c',1), True)
for s in (100,200,400,600,800,1000):
    t(f'good 359fcc3c m{s}', lambda s=s: E.parse_done(good('359fcc3c',s),'359fcc3c',s), False)
t('step 600 receipt naming m800', lambda: E.parse_done(good('359fcc3c',800),'359fcc3c',600), True)
t('step 600 receipt naming m60', lambda: E.parse_done(good('359fcc3c',60),'359fcc3c',600), True)
t('step 1000 receipt naming mstop', lambda: E.parse_done(b'q8/8865619b/359fcc3c_mstop.tar 5 '+sha.encode()+b'\n','359fcc3c',1000), True)
t('run 469ddece receipt as 359fcc3c', lambda: E.parse_done(good('469ddece',600),'359fcc3c',600), True)
t('other lineage', lambda: E.parse_done(good('359fcc3c',600).replace(b'8865619b',b'd2d30e36'),'359fcc3c',600), True)
t('gs:// prefixed', lambda: E.parse_done(b'gs://cmu-gpucloud-jjyeung/'+good('359fcc3c',600),'359fcc3c',600), True)
t('JSON form', lambda: E.parse_done(json.dumps(dict(object='q8/8865619b/359fcc3c_m600.tar',bytes=5,sha256=sha)).encode(),'359fcc3c',600), True)
t('CRLF', lambda: E.parse_done(good('359fcc3c',600).replace(b'\n',b'\r\n'),'359fcc3c',600), True)
t('two lines', lambda: E.parse_done(good('359fcc3c',600)*2,'359fcc3c',600), True)
t('zero bytes', lambda: E.parse_done(f'q8/8865619b/359fcc3c_m600.tar 0 {sha}\n'.encode(),'359fcc3c',600), True)
t('uppercase sha', lambda: E.parse_done(f'q8/8865619b/359fcc3c_m600.tar 5 {"A"*64}\n'.encode(),'359fcc3c',600), True)
t('unknown run', lambda: E.parse_done(good('deadbeef',600),'deadbeef',600), True)
# validate_request on prepared configs
d=Path(tempfile.mkdtemp(dir='/scratch/jjyeung/orch_n30/review_d0r2/tmp'))
for s in (600,800,1000):
    cfg=L.prepare('a'+uuid.uuid4().hex[:12], d/f'p{s}', s)
    t(f'prepared {s} validates', lambda c=cfg: L.validate_request(c), False)
    c2=copy.deepcopy(cfg); c2['spec']['step']=s-200 if s!=1000 else 800
    t(f'{s}: spec step changed, plan hash not', lambda c=c2: L.validate_request(c), True)
    c3=copy.deepcopy(cfg); c3['spec']['artifact']['path']=c3['spec']['artifact']['path'].replace('359fcc3c','469ddece'); c3['plan_sha256']=L.canonical(c3['spec'])
    t(f'{s}: artifact run 469ddece, plan re-hashed', lambda c=c3: L.validate_request(c), True)
    c4=copy.deepcopy(cfg); c4['spec']['artifact']['path']=c4['spec']['artifact']['path'].replace(f'/m{s}/','/m400/'); c4['plan_sha256']=L.canonical(c4['spec'])
    t(f'{s}: artifact m400, plan re-hashed', lambda c=c4: L.validate_request(c), True)
    c5=copy.deepcopy(cfg); c5['spec']['step']=700; c5['spec']['artifact']['path']=c5['spec']['artifact']['path'].replace(f'/m{s}/','/m700/'); c5['plan_sha256']=L.canonical(c5['spec'])
    t(f'{s}: consistent step 700', lambda c=c5: L.validate_request(c), True)
t('prepare step 50 refused', lambda: L.prepare('a'+uuid.uuid4().hex[:12], d/'p50', 50), True)
# stage_export: tar rooted at the wrong milestone
w=Path(tempfile.mkdtemp(dir='/tmp')); 
def mktar(root):
    b=io.BytesIO()
    with tarfile.open(fileobj=b,mode='w') as a:
        for n,data in ((root+'/',None),(root+'/artifact.json',b'{}'),(root+'/heads.pt',b'x'),(root+'/full_weights/',None),(root+'/full_weights/full_weights.json',b'{}')):
            ti=tarfile.TarInfo(n.rstrip('/'))
            if data is None: ti.type=tarfile.DIRTYPE; a.addfile(ti)
            else: ti.size=len(data); a.addfile(ti,io.BytesIO(data))
    return b.getvalue()
for tag,root,step in (('m800 tar admitted as 600','m800',600),('m600 tar as 600 (control, reaches room())','m600',600)):
    raw=mktar(root); tp=w/(tag.replace(' ','_')+'.tar'); tp.write_bytes(raw)
    dn=w/(tag.replace(' ','_')+'.json'); dn.write_text(json.dumps(dict(object='q8/8865619b/359fcc3c_m%d.tar'%step,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())))
    r=w/('root_'+root); 
    t(tag, lambda: E.stage_export(NS(root=str(r),run='359fcc3c',step=step,tar=str(tp),done=str(dn),full=True,bwrap='')), True)
t('stage_export run 469ddece-free name deadbeef', lambda: E.stage_export(NS(root=str(w/'x'),run='deadbeef',step=600,tar=str(tp),done=str(dn),full=True,bwrap='')), True)
print('tmpdir', w)
