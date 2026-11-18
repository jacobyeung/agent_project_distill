import hashlib, io, json, os, subprocess, sys, tarfile, tempfile, shutil, copy
from pathlib import Path
R=Path('/scratch/jjyeung/orch_n30/review_h1eval/work'); W=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1eval_repin')
H=W/'in/h1_1_run_inputs'; FILL=W/'out/fill_export.py'
sha=lambda b:hashlib.sha256(b).hexdigest()
def mk(tmp, member='m100'):
    w=b'W'*5000; idx=json.dumps({'weight_map':{'a':'model-1.safetensors'}}).encode()
    full=dict(schema='full-ft-export-v1',dtype='bfloat16',tensor_count=1,files=[dict(name='model-1.safetensors',sha256=sha(w),bytes=len(w))],index=dict(name='model.safetensors.index.json',sha256=sha(idx)))
    fr=json.dumps(full).encode(); heads=b'H'*3000
    art=dict(config_sha256='26a60a5cf1c0d403050b0026bedd3e4ab8b08891fff992cc7ccab8931b92f2ef',base_identity='c202236235762e1c871ad0ccb60c8ee5ba337b9a',frame_layout='duplicate',geometry_online=False,
             heads=dict(sha256=sha(heads)),full_weights=dict(sha256=sha(fr)))
    ar=json.dumps(art).encode(); buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w') as t:
        for n,d in [(member+'/artifact.json',ar),(member+'/heads.pt',heads),(member+'/full_weights/full_weights.json',fr),(member+'/full_weights/model-1.safetensors',w),(member+'/full_weights/model.safetensors.index.json',idx)]:
            i=tarfile.TarInfo(n);i.size=len(d);t.addfile(i,io.BytesIO(d))
    raw=buf.getvalue(); q=len(raw)//4; parts=[raw[:q],raw[q:2*q],raw[2*q:3*q],raw[3*q:]]
    paths=[]
    for k,p in enumerate(parts): f=tmp/f'e{k}'; f.write_bytes(p); paths.append(str(f))
    return raw,paths
def run(name, mut=None, expect_ok=True, step='100', member='m100'):
    tmp=Path(tempfile.mkdtemp(dir=R/'t')); raw,paths=mk(tmp,member); obj='q8/8865619b/17c4ffa4_m100.tar'
    done=f'{obj} {len(raw)} {sha(raw)}\n'; args=dict(parts=paths,done=done,object=obj)
    if mut: mut(args,raw)
    (tmp/'done').write_text(args['done'])
    base=json.loads((W/'in/prod_pkg/a/1.json').read_text()); (tmp/'base.json').write_text(json.dumps(base))
    cmd=[sys.executable,'-I','-B',str(FILL),'--parts',*args['parts'],'--done',str(tmp/'done'),'--object',args['object'],
         '--config',str(H/'node_local/config.json'),'--receipt',str(H/'node_local/prepared/s1_receipt.json'),'--data-receipt',str(H/'inputs/data_receipt.json'),
         '--lineage','SFT','--step',step,'--out',str(tmp/'export.json'),'--prep-tar',str(tmp/'p.tar'),'--base-inputs',str(tmp/'base.json'),'--inputs-out',str(tmp/'1.json')]
    r=subprocess.run(cmd,capture_output=True,text=True); wrote=(tmp/'export.json').exists() or (tmp/'1.json').exists() or (tmp/'p.tar').exists()
    ok=(r.returncode==0 and wrote) if expect_ok else (r.returncode!=0 and not wrote)
    print('PASS' if ok else 'FAIL',name,'rc',r.returncode,'wrote',wrote,(r.stderr.strip().splitlines() or [''])[-1][:110])
    return ok, tmp
res=[]
ok,tmp=run('valid four parts emit'); res.append(ok)
e=json.loads((tmp/'export.json').read_text()); i=json.loads((tmp/'1.json').read_text())
print('  member',e['member_directory'],'step',e['step'],'types',i['types'],'prep receipt sha',e['preparation']['receipt']['sha256'][:8],'export_pin ok',i['export_pin']['sha256']==sha((tmp/'export.json').read_bytes()))
res.append(run('wrong .done sha',lambda a,r:a.update(done=a['done'].replace(sha(r),'0'*64)),False)[0])
res.append(run('wrong .done bytes',lambda a,r:a.update(done=a['done'].replace(str(len(r)),str(len(r)+1))),False)[0])
res.append(run('parts reordered',lambda a,r:a.update(parts=[a['parts'][1],a['parts'][0]]+a['parts'][2:]),False)[0])
res.append(run('part missing',lambda a,r:a.update(parts=a['parts'][:3]),False)[0])
res.append(run('object differs',lambda a,r:a.update(object='q8/8865619b/469ddece_m100.tar'),False)[0])
def tamper(a,r):
    p=Path(a['parts'][3]); b=bytearray(p.read_bytes()); b[-1]^=1; p.write_bytes(bytes(b))
res.append(run('trailing byte tampered',tamper,False)[0])
ok,_=run('step label inconsistent with member dir m100 (--step 544) is NOT refused',step='544'); print('  -> label cross-check absent' if ok else '  -> refused')
ok,_=run('5 parts (extra empty) still emits',lambda a,r:(Path(a['parts'][0]).with_name('e4').write_bytes(b''),a['parts'].append(str(Path(a['parts'][0]).with_name('e4'))))); print('  -> part count not enforced' if ok else '')
print('ALL PASS' if all(res) else 'SOME FAIL',sum(res),'/',len(res))
