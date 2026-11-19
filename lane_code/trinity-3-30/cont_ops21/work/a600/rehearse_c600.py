"""Bounded local rehearsal; model archives are sparse header fixtures, never weights.

Run with p1cpu Python. All writes stay in the supplied new output directory.
The two policy script bodies are unavailable; dry2 reports their hashes as failures.
No production hash check is disabled or changed.
"""
import ast
import copy
import difflib
import hashlib
import io
import json
import os
import resource
import runpy
import subprocess
import sys
import tarfile
from pathlib import Path

H = Path(__file__).resolve().parent
W = (H/(sys.argv[1] if len(sys.argv)>1 else 'rehearsal')).resolve()
assert W.is_relative_to(H) and not W.exists()
W.mkdir()
resource.setrlimit(resource.RLIMIT_AS, (15*1024**3, 15*1024**3))
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[k] = '1'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
PY = sys.executable
sha = lambda d: hashlib.sha256(d).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
def write(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, indent=2, sort_keys=True)+'\n')
def untar(raw):
    with tarfile.open(fileobj=io.BytesIO(raw)) as t:
        return {m.name:t.extractfile(m).read() for m in t if m.isfile()}
def put_files(root, files):
    for n,d in files.items():
        p=root/n; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(d)
def run(args, log, env=None, expected=0):
    with (W/log).open('w') as f:
        r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,env=env)
    assert r.returncode==expected, (args, r.returncode, str(W/log))

# Seed only the small reviewed source and metadata required by the builder.
K=W/'k'; olddir=K/'a15_cot_ap1f6dfa8874e49e1e'; olddir.mkdir(parents=True)
original=(H/'in/origA_1.tgz').read_bytes()
assert sha(original)=='ca977dd2bc6feb1c14c7c03023eefe7b5e2b67b1cabe838d34effbafd003c765'
(olddir/'1.tgz').write_bytes(original)
orig=untar(original)
with tarfile.open(str(H/'in/ref/A10b_pkg.tar')) as t:
    ref={m.name.split('/',1)[1]:t.extractfile(m).read() for m in t if m.isfile()}
base=json.loads(orig['a/0.json']); oldfilled=json.loads(ref['a/1.json'])
oldfilled['archives'][4]=oldfilled['archives'].pop()
put_files(K/'a15_cot_apd72cdcff1e22a', {'a/0.json':orig['a/0.json'], 'a/1.json':json.dumps(oldfilled).encode()})
env=dict(os.environ,KROOT=str(K))
for name,builder,binding in [('r400','in/build_r10.py','in/BIND400.json'),('r600','build_r11.py','in/BIND600.json')]:
    stage=W/name; stage.mkdir()
    run([PY,'-B',str(H/builder),str(stage),'A',str(H/binding)],name+'.log',env)
reports={n:read(W/n/'BUILD.json')['A'] for n in ('r400','r600')}
new=untar(Path(reports['r600']['delivery_dir'],'1.tgz').read_bytes())
four=untar(Path(reports['r400']['delivery_dir'],'1.tgz').read_bytes())
P=Path(reports['r600']['package']); put_files(P,new); (P/'a').chmod(0o700)
pay=untar(new['0.tgz']); pub=json.loads(new['0.json']); cfg=json.loads(pay['9.json'])

def bundle(d):
    line=next(x for x in d.decode().splitlines() if x.startswith('b=bytes.fromhex('))
    return untar(bytes.fromhex(ast.literal_eval(ast.parse(line).body[0].value.args[0])))
def normalized(files, token):
    out={n:d.replace(token.encode(),b'TOKEN') for n,d in files.items() if n not in ('0.tgz','BATCH.sh','0.json','CONFIG.json','PACKAGE.json')}
    out.update({'payload/'+n:d.replace(token.encode(),b'TOKEN') for n,d in untar(files['0.tgz']).items()})
    out.update({'bundle/'+n:d.replace(token.encode(),b'TOKEN') for n,d in bundle(files['BATCH.sh']).items() if n!='0.json'})
    shell='\n'.join(x for x in files['BATCH.sh'].decode().splitlines() if not x.startswith('b=bytes.fromhex('))
    out['batch-shell']=shell.replace(token,'TOKEN').encode()
    return out
# The fresh step-400 replay must match the actual A10b build before using it as a comparator.
ref_delivery={n:ref[n] for n in orig}
ref_delivery['a/1.json']=orig['a/1.json']; ref_delivery['a/export.json']=orig['a/export.json']
assert normalized(four,reports['r400']['token'])==normalized(ref_delivery,'dc76460c3a164')

inventory=[]; diff=[]
def compare(layer,a,b):
    assert set(a)==set(b),layer
    for n in sorted(a):
        x,y=a[n],b[n]; changed=x!=y
        inventory.append(dict(layer=layer,member=n,changed=changed,old_sha256=sha(x),new_sha256=sha(y)))
        diff.append('%s %s/%s\n' % ('CHANGED' if changed else 'IDENTICAL',layer,n))
        if changed and n not in ('0.tgz','BATCH.sh'):
            try:
                tx,ty=x.decode(),y.decode()
                if n.endswith('.json'):
                    tx=json.dumps(json.loads(tx),indent=2,sort_keys=True)+'\n'
                    ty=json.dumps(json.loads(ty),indent=2,sort_keys=True)+'\n'
                diff.extend(difflib.unified_diff(tx.splitlines(True),ty.splitlines(True),'A10b/'+layer+'/'+n,'C600/'+layer+'/'+n))
            except (UnicodeDecodeError,ValueError):
                diff.append('SHA256 %s -> %s\n' % (sha(x),sha(y)))
compare('delivery',ref_delivery,new)
refpay=untar(ref['0.tgz'])
compare('payload',refpay,pay)
compare('bundle',bundle(ref['BATCH.sh']),bundle(new['BATCH.sh']))
shell=lambda d:'\n'.join(x for x in d.decode().splitlines() if not x.startswith('b=bytes.fromhex('))+'\n'
diff.extend(difflib.unified_diff(shell(ref['BATCH.sh']).splitlines(True),shell(new['BATCH.sh']).splitlines(True),'A10b/BATCH-shell','C600/BATCH-shell'))
(W/'DIFF_A10b_C600.txt').write_text(''.join(diff)); write(W/'MEMBERS.json',inventory)
allowed={'0.json','CONFIG.json','PACKAGE.json','BATCH.sh','0.tgz','a/0.json','a/4.py','a/6.py'}
assert {n for n in new if new[n]!=ref_delivery[n]}==allowed
assert [n for n,d in pay.items() if d!=refpay[n]]==['9.json']
assert normalized(new,pub['token'])['batch-shell']==normalized(ref_delivery,'dc76460c3a164')['batch-shell']
assert pay['items/devs1_routed.json']==refpay['items/devs1_routed.json']

# Use real preparation bytes (identical at 400 and 600), with simulated large-file scan metadata.
fixtures=W/'fixtures'; fixtures.mkdir()
prep=untar(ref['a/6']); put_files(fixtures,prep)
b=read(H/'in/BIND600.json'); export=json.loads(ref['a/export.json'])
for k in ('run','step','member_directory','object','config_sha256','archive_sha256'):
    export[k]=b[k]
artifact=dict(step=600,config_sha256=b['config_sha256'],base_identity=b['base_identity'],frame_layout=b['frame_layout'],geometry_online=False)
for name,rel in [('heads','heads.pt'),('full_weights','full_weights/full_weights.json')]:
    artifact[name]=dict(path='/synthetic/'+b['run']+'/m600/'+rel,sha256=export[name]['sha256'])

# Sparse tar files contain only headers plus small JSON. No weight data is read or written.
def sparse_tar(path, members, total=None):
    with path.open('xb') as f:
        for name,size,data,isdir in members:
            m=tarfile.TarInfo(name); m.size=size; m.mode=0o700 if isdir else 0o600
            if isdir:m.type=tarfile.DIRTYPE
            f.write(m.tobuf(format=tarfile.USTAR_FORMAT)); start=f.tell()
            if data is not None:
                assert len(data)<=size,(name,len(data),size)
                f.write(data)
            f.seek(start+((size+511)//512)*512)
        f.write(b'\0'*1024)
        if total:
            assert f.tell()<total; f.seek(total-1); f.write(b'\0')
    return path.stat().st_size
simbase=copy.deepcopy(base); simbase['types']=cfg['order'][:3]
logical=cfg['logical']+'/d/'
groups={i:[] for i in range(1,5)}
slot={'g3t_weights':1,'g3t_config':1,'sam_checkpoint':3,'sam_receipt':3,'policy':4,'env':4}
for name,spec in simbase['files'].items():
    if name in ('artifact','heads','full_weights'):continue
    data=None
    if name=='policy':data=json.dumps(dict(authorized=True,**simbase['policy'])).encode()
    if name=='env':data=json.dumps(dict(versions={})).encode()
    if data:data=data+b' '*(spec['bytes']-len(data))
    groups[slot.get(name,2)].append((spec['path'][len(logical):],spec['bytes'],data,False))
groups[2]+=[('v/py',1,b'x',False),('f',0,None,True),('s',0,None,True)]
for name in ('vnice','terminator'):
    raw=('#!/bin/bash\n# Unavailable %s policy body: local fixture only.\nexit 99\n'%name).encode()
    groups[4].append(('q/'+name+'.sh',len(raw),raw,False))
for i in range(1,5):
    path=fixtures/('slot%d.tar'%i); size=sparse_tar(path,groups[i])
    simbase['archives'][i]['parts']=[dict(path=str(path),bytes=size,sha256=base['archives'][i]['sha256'])]
write(fixtures/'base.json',simbase)
members=[]
for name,rel in [('artifact','artifact.json'),('heads','heads.pt'),('full_weights','full_weights/full_weights.json')]:
    members.append(('m600/'+rel,export[name]['bytes'],None,False))
partsize=b['archive_bytes']//4; parts=[]
for i in range(4):
    path=fixtures/str(i); sparse_tar(path,members if i==0 else [],partsize)
    parts.append(dict(path=str(path),bytes=partsize,sha256='0'*64))
archive=dict(destination=base['archives'][0]['destination'],expanded_bytes=base['archives'][0]['expanded_bytes'],parts=parts,sha256=b['archive_sha256'])
done=fixtures/'done'; done.write_text('%s %d %s\n'%(b['object'],b['archive_bytes'],b['archive_sha256']))
mod=runpy.run_path(str(P/'a/4.py'),run_name='fixture_fill')
mod['main'].__globals__['scan']=lambda *args:(copy.deepcopy(export),copy.deepcopy(artifact),copy.deepcopy(archive))
sys.argv=['4.py','--parts']+[p['path'] for p in parts]+['--done',str(done),'--object',b['object'],'--config',str(fixtures/'p0/config.json'),'--receipt',str(fixtures/'p0/receipt.json'),'--data-receipt',str(fixtures/'p0/data_receipt.json'),'--lineage','SFT','--step','600','--out',str(P/'a/export.json'),'--prep-tar',str(P/'a/6'),'--base-inputs',str(fixtures/'base.json'),'--inputs-out',str(P/'a/1.json')]
mod['main']()
assert read(P/'a/1.json')['types']==cfg['order'][:3]
assert len(read(P/'a/1.json')['archives'])==6
run([PY,'-B',str(H/'in/dryres2.py'),str(P/'a/1.json'),str(fixtures/'base.json'),sha((P/'a/6').read_bytes())],'dryres.json')
# The local 3.py check uses only namespace remapping; no cryptographic check changes.
adapter=W/'local_check.py'
adapter.write_text('''import builtins,sys,runpy
from pathlib import Path
original=builtins.compile
k=sys.argv[2]
def compile_local(source,filename,mode,*args,**kwargs):
    if isinstance(source,(str,bytes)):
        raw=source.decode() if isinstance(source,bytes) else source
        raw=raw.replace("'/project/community/jjyeung/okh7'",repr(k))
        raw=raw.replace("'/project/community/jjyeung/'",repr(k.rsplit('/',1)[0]+'/'))
        source=raw
    return original(source,filename,mode,*args,**kwargs)
builtins.compile=compile_local
p=sys.argv[1];sys.argv=[p,'check','--gpus','1','--time','03:00:00']
runpy.run_path(p,run_name='__main__')
''')
run(['/usr/bin/python3','-B',str(adapter),str(P/'3.py'),str(K)],'check3.json')
run(['/usr/bin/python3','-B',str(H/'dry2_c600.py'),str(P),str(W/'drywork')],'dry2.json',expected=1)
d=read(W/'dry2.json')
assert d['failed']==['stage.vnice_sha','stage.terminator_sha'],d['failed']

times={}
for i,kind in enumerate(cfg['order']):
    p=H/('in/out3/A10b/ret/metadata/reads/0/metadata/journals/%d/0/timings.jsonl'%i)
    times[kind]=sum(json.loads(line)['seconds'] for line in p.read_text().splitlines())
write(W/'TIMING.json',dict(per_type_seconds=times,camera_seconds=sum(times[k] for k in cfg['order'][:3]),
    first_load_seconds=76.5924266850052,walltime='03:00:00',walltime_seconds=10800,stop_margin=1800,return_margin=1200,
    sizing='1.25 * (camera seconds + first load seconds) + 1800 stop + 1200 return + 3000 startup allowance < 10800'))
write(W/'RESULT.json',dict(package=str(P),build=reports['r600'],reference_rebuild_matches_A10b=True,
    dryres_passed=True,check3_passed=True,dry2_unavailable=d['failed'],
    simulation=['scan() replaced by reviewed-shape metadata; no real weights available',
                'sparse archive headers with declared sizes; large-file hashes not exercised',
                'real preparation bytes and original fill bind_review/receipt_review executed',
                'two absent policy scripts are explicit placeholders and fail their unchanged hash checks',
                '3.py check remaps Orchard paths to local workspace paths in memory only']))
print('Rehearsal complete:',W)
print('dryres and local 3.py check PASS; dry2 has exactly two unavailable policy-body checks.')
