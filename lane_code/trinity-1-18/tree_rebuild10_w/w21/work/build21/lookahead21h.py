"""Run the unchanged decoded kit in the retained build-21g stand-in view."""
from pathlib import Path
import datetime,json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21h';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
D.mkdir(exist_ok=True)
args=J.load(L/'work/build21g/proofs/view/after.json')
view=J.load(L/'work/build21g/VIEW.json');node=Path(view['variables']['Q_ROOT']);ns=view['variables']['Q_NS']
paths={}
for item in J.load(B/'UPLOADS.json')['files']:
    p=Path(item['local_path'])
    assert not str(p).startswith(('/home/','/data'))
    if p.is_file():
        assert J.sha(p)==item['sha256']
        paths[item['sha256']]=str(p)
cfg=J.load(K/'k/n.json');cfgpin=J.write(node/'h_config.json',cfg)
request=J.load(K/'k/r.json');spec=J.load(K/'k/p.json')
request.update(config=cfgpin,staged_pins=[dict(path=p,sha256=h) for h,p in paths.items()]+[cfgpin],
    room_audit=cfg['r1_training']['room_audit'],frame_roots=spec['frame_roots'],milestone=400,
    device='cpu',memory_gib=16,_paths=paths)
J.write(node/'h_request.json',request)
records=[]
for label,command in [('view',args+['/usr/bin/true']),
    ('native_kitq',args+[sys.executable,'-s','-B',str(K/'b/a.py'),'q',ns+'/hbefore',ns+'/h_request.json'])]:
    p=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    records.append(dict(stage=label,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
result=J.load(node/'hbefore/q/RESULT.json')
assert records[0]['returncode']==0
assert result['refusal']=='ValueError:R1_PROOF_NATIVE_ROUTING_REQUIRED'
J.write(D/'LOOKAHEAD_BEFORE.json',dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),GO=False,
    kit_seal=J.seal(K),config_source='work/build21/kits/q/k/n.json',decoded_config_sha256=cfgpin['sha256'],
    config_unchanged=True,command=args,runs=records,result=result,request=request,
    stand_ins=['CPU Python instead of staged GPU environment; the independent GPU guard was already checked by build 21g.',
               'Same empty source directories and prefixed AS/AL/P destinations as build 21g; no config substitution.']))
print(json.dumps(dict(runs=records,refusal=result['refusal'])))
