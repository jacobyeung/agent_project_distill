from pathlib import Path
import datetime,json,subprocess,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';B=L/'work/build21'
sys.path[:0]=[str(D),str(B),str(L/'work/tree_r1')]
import joblib as J
old=str(L.parent/'w21');args=[x.replace(old,str(L)) for x in J.load(L/'work/build21g/proofs/view/after.json')]
for i,x in enumerate(args):
    if x in ('--bind','--ro-bind'):
        for raw in args[i+1:i+3]:
            p=Path(raw)
            if p.is_relative_to(L):p.mkdir(parents=True,exist_ok=True)
view=J.load(L/'work/build21g/VIEW.json');node=Path(view['variables']['Q_ROOT'].replace(old,str(L)));ns=view['variables']['Q_NS']
results={}
for name,step in (('q',400),('n',400)):
    k=L/'work/build24/kits'/name;paths={x['sha256']:x['local_path'] for x in J.load(D/('UPLOADS_'+name+'.json'))['files'] if x['opaque_name'].startswith('u/')}
    cfg=J.load(k/'k/n.json');cfgpin=J.write(node/(name+'_config.json'),cfg)
    request=J.load(k/'k/r.json');spec=J.load(k/'k/p.json')
    request.update(config=cfgpin,staged_pins=[dict(path=p,sha256=h) for h,p in paths.items()]+[cfgpin],room_audit=cfg['r1_training']['room_audit'],frame_roots=spec['frame_roots'],milestone=step,device='cpu',memory_gib=16,_paths=paths)
    J.write(node/(name+'_request.json'),request)
    directory='b24b_'+name+'_'+J.seal(k)[:8]
    runs=[]
    for label,cmd in [('view',args+['/usr/bin/true']),('gpu_guard',args+[sys.executable,'-s','-B',str(k/'b/g.py')]),('own_config',args+[sys.executable,'-s','-B',str(k/'b/a.py'),'q',ns+'/'+directory,ns+'/'+name+'_request.json'])]:
        p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        runs.append(dict(stage=label,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
    result=J.load(node/directory/'q/RESULT.json') if (node/directory/'q/RESULT.json').exists() else None
    results[name]=dict(GO=False,kit_seal=J.seal(k),own_config_unchanged=True,decoded_config_sha256=cfgpin['sha256'],
        runs=runs,result=result,stand_ins=['CPU interpreter and empty production mount sources in the inherited bwrap view'],
        classification='boundary' if result and result.get('refusal')=='ValueError:R1_PROOF_FRAME_HOST_REQUIRED' else 'defect')
    J.write(D/('LOOKAHEAD_'+name+'.json'),results[name]);print(name,results[name]['classification'],result.get('refusal') if result else runs)
