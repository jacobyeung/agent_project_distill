"""Exercise decoded staging and post-staging helpers on writable CPU kit copies."""
from pathlib import Path
import ast,base64,hashlib,importlib.util,json,os,shlex,subprocess,sys,unittest
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24c';T=L/'work/tree_r1'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build21'),str(T)]
import joblib as J
from launch_r1.build import verify

def files(k):return {str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file()}

records={}
for name in ('q','n'):
 root=D/'sequence'/name;root.mkdir(parents=True,exist_ok=True)
 (root/'operator').mkdir(exist_ok=True)
 source=(L/'work/build21/jobtest.py').read_text()
 source=source.replace('L=Path(__file__).resolve().parents[2]', 'L=Path('+repr(str(L))+')')
 source=source.replace("L/'work/build21/proofs/job'",'Path('+repr(str(root))+')')
 source=source.replace("B/'kits/q'",f"L/'work/build24/kits/{name}'")
 source=source.replace("B/'proofs/operator/",f"L/'work/build24c/sequence/{name}/operator/")
 source=source.replace("cls.spec['uploads']=[];", "cls.spec.pop('m4',None);cls.spec['uploads']=[];")
 source=source.replace("source=dict(streams={},s1_routing={},preparation_output='/opaque/p')", "fixture_cfg=J.load(cls.kit/'k/n.json');fixture_cfg['r1_training'].pop('init_policy',None);(cls.kit/'k/n.json').write_bytes(capsule_json(fixture_cfg))\n        source=dict(streams={},s1_routing={},preparation_output='/opaque/p')")
 source=source.replace("source=dict(streams={},s1_routing={},preparation_output='/opaque/p')", "source=dict(streams={'routing':J.load(cls.kit/'k/n.json')['streams']['routing']},s1_routing=J.load(cls.kit/'k/n.json')['s1_routing'],preparation_output='/opaque/p')")
 source=source.replace("dict(model=model,streams={},config_sha256=", "dict(model=model,streams={key:dict(receipt=value) for key,value in source['streams'].items()},config_sha256=")
 # Audit the exact writable fixture kit immediately around the complete job
 # shell. The fixture changes only pinned transport data and local paths.
 source=source.replace("with (L/'work/build24c/sequence/", "with (L/'work/build24c/sequence/")
 filename=root/'fixture.py';filename.write_text(source)
 module_spec=importlib.util.spec_from_file_location('seq_'+name,filename);M=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(M)
 M.Job20.setUpClass();case=M.Job20('test_shell_stage_and_namespace')
 real_run=subprocess.run;stage={}
 def run(*args,**kw):
  cmd=args[0] if args else kw['args']
  is_job=len(cmd)>1 and cmd[0]=='/bin/bash' and cmd[1]==str(case.kit/'job.sh')
  if is_job:stage['before']=files(case.kit);verify(case.kit)
  result=real_run(*args,**kw)
  if is_job:
   stage['after']=files(case.kit);assert stage['after']==stage['before'];verify(case.kit)
  return result
 with patch.object(subprocess,'run',side_effect=run):case.test_shell_stage_and_namespace()
 assert stage['before']==stage['after']
 k=case.kit;node=root/'q_22c714e1_20'
 # Fixture's full decoded tk_stage sequence ran the real archive/staging
 # helpers, including m.py/s.py and Q_CAPTURE's w.py. Reuse its writable kit
 # for the exact decoded post-staging pipeline in the CPU stand-in view.
 shell=base64.b64decode(J.load_raw(k/'k/j.json')['payload']).decode()
 tail=shell[shell.rindex('\ntk_stage full')+1:]
 tail=tail[tail.index('"${BW[@]}" "$PILOT_VENV/bin/python"'):]
 old=str(L.parent/'w21');view=J.load(L/'work/build21g/proofs/view/after.json')
 args=[x.replace(old,str(L)) for x in view]
 ns=J.load(k/'k/p.json')['namespace']
 args+=['--bind',str(node),str(node),'--bind',str(node),ns,'--bind',str(k),str(k)]
 cfg=J.load(L/'work/build24/kits'/name/'k/n.json');cfgpin=J.write(node/'own.json',cfg)
 paths={x['sha256']:x['local_path'] for x in J.load(D/('UPLOADS_'+name+'.json'))['files'] if x['opaque_name'].startswith('u/')}
 request=J.load(k/'k/r.json');request.update(config=cfgpin,staged_pins=[dict(path=p,sha256=h) for h,p in paths.items()]+[cfgpin],room_audit=cfg['r1_training']['room_audit'],frame_roots=J.load(k/'k/p.json')['frame_roots'],milestone=400,device='cpu',memory_gib=16,_paths=paths)
 J.write(node/'r.json',request)
 # Empty stream fixture exercises the real room helper and pinned authority
 # without scanning production databases; own-config admission is unchanged.
 roomcfg=json.loads(json.dumps(cfg));roomcfg['streams']={};J.write(node/'n.json',roomcfg)
 guard=node/'guard.py';guard.write_text('''import runpy,sys
from types import SimpleNamespace
sys.modules['torch']=SimpleNamespace(__version__='cpu-fixture',cuda=SimpleNamespace(is_available=lambda:True,device_count=lambda:1,get_device_properties=lambda i:SimpleNamespace(name='CPU fixture',total_memory=85017493504)))
runpy.run_path(sys.argv[1],run_name='__main__')
''')
 tail=tail.replace('"$Q_KIT/b/g.py"',shlex.quote(str(guard))+' "$Q_KIT/b/g.py"')
 prelude='set -euo pipefail\nexport PYTHONDONTWRITEBYTECODE=1\nBW=('+shlex.join(args)+')\n'
 env={**os.environ,'Q_KIT':str(k),'Q_ROOT':str(node),'Q_NS':ns,'PILOT_VENV':str(Path(sys.executable).parent.parent),'SLURM_JOB_ID':'20','PYTHONDONTWRITEBYTECODE':'1'}
 script=node/'tail.sh';script.write_text(prelude+tail)
 before=files(k);verify(k)
 p=real_run(['/bin/bash',str(script)],env=env,cwd=node,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 (node/'tail.stdout').write_text(p.stdout);(node/'tail.stderr').write_text(p.stderr)
 result=J.load(node/'p/q/RESULT.json')
 assert result['refusal']=='ValueError:R1_PROOF_FRAME_HOST_REQUIRED',result
 publication=Path(J.load(k/'k/p.json')['n_root'])/'o/20/RESULT.json'
 rc=J.load(publication);assert rc['proof_rc']==1 and rc['rooms_rc']==0,rc
 if name=='n':
  line=next(x for x in shell.splitlines() if '"$Q_KIT/b/t.py"' in x)
  p2=real_run(['/bin/bash','-c',prelude+line],env=env,cwd=node,capture_output=True,text=True);assert p2.returncode==0,p2.stderr
 after=files(k);assert after==before;seal=verify(k)
 assert not list(k.rglob('*.pyc'))
 records[name]=dict(status='PASS',writable_kit=str(k),fixture_kit_seal=seal,production_kit_seal=J.seal(L/'work/build24/kits'/name),staging_unchanged=stage['before']==stage['after'],pipeline_unchanged=before==after,file_count=len(after),snapshot=after,refusal=result['refusal'],proof_rc=rc['proof_rc'],rooms_rc=rc['rooms_rc'],helpers=['m','s','w','g','a','l','d','l']+(['t','l'] if name=='n' else [])+['o'],stand_ins=['Tiny archive/store/transport fixtures through native staging','CPU Python replaces host interpreter','CPU torch diagnostic stand-in only for g.py','Existing CPU bwrap view','Room report uses empty streams and real pinned authority','GO=false launcher returns before distributed training'])
 J.write(D/'SEQUENCE.json',records);print(name,'decoded staging and pipeline unchanged',len(after),'files',flush=True)
