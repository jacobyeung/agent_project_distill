"""Run the decoded job shell through all reachable helpers in job order."""
from pathlib import Path
import ast,base64,hashlib,importlib.util,json,os,shlex,subprocess,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24k';T=L/'work/tree_r1'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build21'),str(T)]
import joblib as J
from launch_r1.build import verify
def files(k):return {str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file()}
records={}
for name in ('q','n'):
 root=D/'sequence_native'/name;root.mkdir(parents=True,exist_ok=True);(root/'operator').mkdir(exist_ok=True)
 source=(L/'work/build21/jobtest.py').read_text()
 source=source.replace('L=Path(__file__).resolve().parents[2]', 'L=Path('+repr(str(L))+')')
 source=source.replace("L/'work/build21/proofs/job'",'Path('+repr(str(root))+')')
 source=source.replace("B/'kits/q'",f"L/'work/build24/kits/{name}'")
 source=source.replace("B/'proofs/operator/",f"L/'work/build24k/sequence_native/{name}/operator/")
 source=source.replace("cls.spec['uploads']=[];", "cls.spec.pop('m4',None);cls.spec['host_paths']={};cls.spec['uploads']=[];")
 source=source.replace("source=dict(streams={},s1_routing={},preparation_output='/opaque/p')", "fixture_cfg=J.load(cls.kit/'k/n.json');fixture_cfg['r1_training'].pop('init_policy',None);(cls.kit/'k/n.json').write_bytes(capsule_json(fixture_cfg))\n        source=dict(streams={'routing':J.load(cls.kit/'k/n.json')['streams']['routing']},s1_routing=J.load(cls.kit/'k/n.json')['s1_routing'],preparation_output='/opaque/p')")
 source=source.replace("dict(model=model,streams={},config_sha256=", "dict(model=model,streams={key:dict(receipt=value) for key,value in source['streams'].items()},config_sha256=")
 # The allocation boundary supplies CPU Python and the inherited native view.
 node=root/'q_22c714e1_20';ns='/tmp/q_22c714e1';k=root/'kit'
 args=['/usr/bin/bwrap','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--ro-bind','/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu','/opt/py','--ro-bind','/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages','/opt/site','--setenv','PYTHONPATH','/opt/site','--bind',str(node),ns,'--ro-bind',str(k),'/tmp/kit','--ro-bind',str(root),'/tmp/fixture','--chdir',ns]
 args += ['--ro-bind',str(root),str(root)]
 for item in J.load(D/('UPLOADS_'+name+'.json'))['files']:
  if item['opaque_name'].startswith('u/'):args += ['--ro-bind',item['local_path'],'/tmp/up/'+item['sha256']]
 J.write(root/'view.json',args)
 guard=root/'guard.py';guard.write_text('''import runpy,sys
import torch
from types import SimpleNamespace
torch.cuda.is_available=lambda:True
torch.cuda.device_count=lambda:1
torch.cuda.get_device_properties=lambda i:SimpleNamespace(name='CPU fixture',total_memory=85017493504)
runpy.run_path(sys.argv[1],run_name='__main__')
''')
 cfg=J.load(L/'work/build24/kits'/name/'k/n.json');cfgpin=J.write(root/'own.json',cfg)
 paths={x['sha256']:'/tmp/up/'+x['sha256'] for x in J.load(L/'work/build24k'/('UPLOADS_'+name+'.json'))['files'] if x['opaque_name'].startswith('u/')}
 request=J.load(L/'work/build24/kits'/name/'k/r.json');cfgpin['path']='/tmp/fixture/own.json'
 request.update(config=cfgpin,staged_pins=[dict(path=p,sha256=h) for h,p in paths.items()]+[cfgpin],room_audit=cfg['r1_training']['room_audit'],frame_roots=J.load(L/'work/build24/kits'/name/'k/p.json')['frame_roots'],milestone=400,device='cpu',memory_gib=16,_paths=paths)
 J.write(root/'request.json',request)
 roomcfg=json.loads(json.dumps(cfg));roomcfg['streams']={};J.write(root/'roomcfg.json',roomcfg)
 boundary=root/'boundary.py';boundary.write_text('from pathlib import Path\nimport shutil,sys,json\nr=Path(sys.argv[1]);s=Path(sys.argv[2])\nv=json.loads((r/"r.json").read_text());req=json.loads((s/"request.json").read_text())\nv["_resolved"]["config"]=json.loads((s/"own.json").read_text());v["_paths"]=req["_paths"]\n(r/"r.json").write_text(json.dumps(v))\nshutil.copyfile(s/"roomcfg.json",r/"n.json")\n')
 injection='\n'+shlex.quote(sys.executable)+' -B '+shlex.quote(str(boundary))+' "$Q_ROOT" '+shlex.quote(str(root))+'\nBW=('+shlex.join(args)+')\nPILOT_VENV='+shlex.quote('/opt/py')+'\n'
 marker="        (self.kit/'k/j.json').write_bytes(rawcap(shell.encode()));reseal(self.kit)"
 replacement="        shell=shell.replace('BW+=(--bind \"$Q_ROOT\" \"$Q_NS\" --setenv TK_JOB_START \"${TK_JOB_START:?}\")','BW+=(--bind \"$Q_ROOT\" \"$Q_NS\")');shell=shell.replace('OMP_NUM_THREADS=48 MKL_NUM_THREADS=48 OPENBLAS_NUM_THREADS=48','OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8');shell=shell.replace('BW+=(--bind \"$Q_ROOT\" \"$Q_NS\")', 'BW+=(--bind \"$Q_ROOT\" \"$Q_NS\")'+"+repr(injection)+")\n"
 replacement+="        shell=shell.replace('\"$Q_KIT/b/g.py\"',"+repr('/tmp/fixture/guard.py /tmp/kit/b/g.py')+")\n"+marker
 replacement=replacement.replace(marker,"        shell=shell.replace('\"$Q_KIT/b/a.py\"','/tmp/kit/b/a.py').replace('\"$Q_KIT/b/d.py\"','/tmp/kit/b/d.py')\n"+marker)
 assert marker in source;source=source.replace(marker,replacement)
 # The fixture supplies only a reviewed selection pin and authentic small inputs;
 # the unavailable production database remains the stopping boundary.
 setup="        spec=deepcopy(self.spec);spec['p_files']=pfiles"
 inject="""
        prod=J.load(L/'work/build24/kits/NAME/k/p.json')
        spec['host_paths']=prod['host_paths']
        spec['uploads']=[dict(sha256=v['sha256'],bytes=v['bytes']) for v in J.load(L/'work/build24k/UPLOADS_NAME.json')['files'] if v['opaque_name'].startswith('u/')]
        spec['pin_paths']={v['sha256']:spec['namespace']+'/u/'+v['sha256'] for v in spec['uploads']}
        source_root=Path(spec['n_root'])/'u';source_root.mkdir(parents=True,exist_ok=True)
        for item in J.load(L/'work/build24k/UPLOADS_NAME.json')['files']:
            if item['opaque_name'].startswith('u/'):shutil.copyfile(item['local_path'],source_root/item['sha256'])
        pin=J.write(self.root/'selected.json',dict(regenerated_sha256='1'*64,rows=1,row_id_digest='2'*64,inputs_pinned={}))
        shutil.copyfile(pin['path'],source_root/pin['sha256'])
        host=J.load(self.kit/'k/h.json');host['routing_selection']=dict(path='u/'+pin['sha256'],sha256=pin['sha256'])
        (self.kit/'k/h.json').write_bytes(capsule_json(host))
""".replace('NAME',name)
 assert setup in source;source=source.replace(setup,setup+inject)

 source=source.replace("'Q_CAPTURE':'1'","'Q_CAPTURE':'0'")
 source=source.replace("        with (L/'work/build24k/sequence_native/","        self.before_job={str(p.relative_to(self.kit)):J.sha(p) for p in self.kit.rglob('*') if p.is_file()}\n        with (L/'work/build24k/sequence_native/")
 a=source.index("        self.assertEqual(r.returncode,0,'See proofs/operator/shell.log')")
 b=source.index('\n    def test_room_report',a)
 source=source[:a]+"        self.last_returncode=r.returncode\n        self.after_job={str(p.relative_to(self.kit)):J.sha(p) for p in self.kit.rglob('*') if p.is_file()}\n        assert self.before_job==self.after_job\n"+source[b:]
 filename=root/'fixture.py';filename.write_text(source)
 sp=importlib.util.spec_from_file_location('seq_'+name,filename);M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M)
 M.Job20.setUpClass();job=k/'job.sh';job.write_text(job.read_text().replace('OMP_NUM_THREADS=48 MKL_NUM_THREADS=48 OPENBLAS_NUM_THREADS=48','OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8'));M.reseal(k);case=M.Job20('test_shell_stage_and_namespace');case.test_shell_stage_and_namespace()
 # Repeat no commands from the job; inspect the artifacts from its one run.
 result=J.load(node/'p/q/RESULT.json') if (node/'p/q/RESULT.json').is_file() else {'refusal':(node/'q.log').read_text().splitlines()[-1]};publication=J.load(Path(J.load(k/'k/p.json')['n_root'])/'o/20/RESULT.json')
 assert result['refusal']=='ValueError:R1_PROOF_FRAME_HOST_REQUIRED' or result['refusal'].startswith(('ValueError: Missing or changed pinned input: ','ValueError: E10:/scratch/fsw/')),result
 assert publication['rooms_rc']==0 and publication['proof_rc']==1,publication
 verify(k);assert not list(k.rglob('*.pyc'))
 records[name]=dict(status='BOUNDARY',hidden_host_roots=['/scratch/jjyeung','/home','/data','/data2','/data3'],production_kit_seal=J.seal(L/'work/build24/kits'/name),kit_bytes_unchanged=case.before_job==case.after_job,writable_kit=str(k),fixture_kit_seal=verify(k),returncode=case.last_returncode,
  stages=[dict(stage=x,status='PASS') for x in ('job.sh:v.py','job.sh:x.py/bootstrap','j.sh:tk_stage full/m.py/s.py','j.sh:tk_env/tk_pythonpath','bwrap','g.py (CUDA query fixture)')]+
   [dict(stage='a.py q / pl.py authenticated planning / l.py',status='BOUNDARY',refusal=result['refusal']),dict(stage='d.py / l.py',status='PASS')]+
   ([dict(stage='h.py / t.py / u.py',status='NOT_REACHED',reason='canary rc=1; shell correctly skips training')] if name=='n' else [])+[dict(stage='o.py',status='PASS')],
  first_refusal=result['refusal'],kit_files=files(k),stand_ins=['CPU interpreter and CUDA property queries','Tiny transport for 9B weights, environment and production stores','Inherited bwrap view with fixture mount sources','Own decoded request config; empty production streams only for room reporting'])
 J.write(D/'SEQUENCE.json',records);print(name,result['refusal'],'rooms and publication PASS',flush=True)
