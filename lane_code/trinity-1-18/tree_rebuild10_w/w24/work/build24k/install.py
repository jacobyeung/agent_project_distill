from pathlib import Path
import sys,json,hashlib,base64,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build24k';T=L/'work/tree_r1'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build24f'),str(T)]
import joblib as J
from kit24f import reseal
from student_pilot.source_seal import inventory,archive,create
from student_pilot.p3_provenance import digest,source_files
from launch_r2.build import capsule_json

def replace(p,raw):
 old=L/'attic/build24k'/p.relative_to(L);old.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and not old.exists():p.rename(old)
 p.write_bytes(raw.encode() if isinstance(raw,str) else raw)

def capsule(raw):
 if not isinstance(raw,bytes):raw=(json.dumps(raw,sort_keys=True,indent=2)+'\n').encode()
 return json.dumps(dict(encoding='base64',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())).encode()

tree=inventory(T);treeh=digest(tree);target=D/('t_'+treeh[:16]+'.tar')
archive(T,target,tree,compress=True)
closure={str(p.relative_to(T)):J.sha(p) for p in source_files([T/'student_pilot/carrier_c1_run.py'])}
for name in ('q','n','n_go'):
 k=L/('out/kit_n_go' if name=='n_go' else 'work/build24/kits/'+name)
 # Retain an exact pre-edit kit, including its immutable seal.
 old=L/'attic/build24k'/k.relative_to(L);old.parent.mkdir(parents=True,exist_ok=True)
 k.rename(old);shutil.copytree(old,k)
 control=J.load(k/'k/a.json');spec=J.load(k/'k/p.json');ns=spec['namespace']+'/p/q'
 (k/control['source']['path']).write_bytes(target.read_bytes())
 control['source'].update(sha256=J.sha(target),tree_sha256=treeh)
 (k/'k/a.json').write_bytes(capsule(control))
 (k/'k/7.json').write_bytes(capsule(dict(schema='c1-sealed-source-v1',commit='sha256:'+treeh,tree_sha256=treeh,files=tree,
     archive={key:control['source'][key] for key in ('path','sha256')},sources=closure,operation_sources=closure)))
 code=create(T,target,closure,{},archive_path=ns+'/t.tar');raw=(json.dumps(code,sort_keys=True,indent=2)+'\n').encode()
 (k/'k/c0.json').write_bytes(capsule(raw));spec['code_sha256']=hashlib.sha256(raw).hexdigest();(k/'k/p.json').write_bytes(capsule(spec))
 cfg=J.load(k/'k/c.json');cfg['code']=dict(path='k/7.json',sha256=J.sha(k/'k/7.json'));(k/'k/c.json').write_bytes(capsule(cfg))
 build=J.load(k/'BUILD.json');build['source_seal']=treeh;(k/'BUILD.json').write_bytes(capsule(build))
 host=J.load(k/'k/h.json');host['routing_selection']={'required_parameter':'R1_ROUTING_SELECTION_PIN_MISSING'}
 (k/'k/h.json').write_bytes(capsule(host))
 for n in ('pl.py','rg.py'):(k/'b'/n).write_bytes((D/n).read_bytes())
 z=(k/'b/z.py').read_text()
 # Keep the authenticated byte copier; all mutable binding work belongs to planning.
 a=z.index('def stage_payload(');b=z.index('\ndef load_raw',a);copier=z[a:b]
 copier=copier.replace('def stage_payload(','def copy_resolved_payload(')
 copier=copier.replace("root/'c.json'","root/'source_code.json'")
 copier=copier.replace("    ns=spec['namespace']","    ns=resolved['_namespace']")
 a2=copier.index("        resolved['paths'][h]=")
 copier=copier[:a2]+"    return None\n"
 z=z[:a]+copier+'''\n# Compatibility entry for resolver refusal tests; production uses pl.plan_payload.
def stage_payload(kit,resolved,root):
    for item in resolved['small_files'].values():
        selected400(item.get('original',item.get('member','')))
        selected400(item.get('member',''))
    raise ValueError('R1_NATIVE_STAGING_HOOK_REQUIRED')
'''+z[b:]
 z=z.replace("    stage_payload(boot_kit,boot_resolved,boot_node)","    write(boot_node/'r.json',dict(_resolved=boot_resolved))")
 (k/'b/z.py').write_text(z)
 a=(k/'b/a.py').read_text().replace("('p','t','q')","('p','t','q','r')").replace("(sys.argv[1]=='q')", "(sys.argv[1] in ('q','r'))")
 a=a.replace('host_entry.frame_host = recorded_host',"if sys.argv[1]=='p':host_entry.frame_host = recorded_host")
 start=a.index("if sys.argv[1]=='q':");end=a.index('from launch_r1.entry import frame_host',start)
 a=a[:start]+'''if sys.argv[1] in ('q','r'):
 from student_pilot.p3_provenance import load
 from student_pilot.r1_persisted import scope
 sys.path.insert(0,str(kit/'b'))
 from pl import plan_payload
 from z import write
 mode=sys.argv[1];incoming=load(sys.argv[3])
 if '_resolved' not in incoming:raise ValueError('R1_STAGING_PLAN_REQUIRED')
 request,paths,stage=plan_payload(kit,incoming['_resolved'],root,regeneration=mode=='r')
 with scope(paths):
  if mode=='q':
   from launch_r1.production_proof import run
   r=run(request,root/'q',stage=stage)
  else:
   import os,shutil
   from launch_r1.entry import begin_host,host_environment,check_host_runtime,stage_host,check_host_scene
   from student_pilot.p3_provenance import pinned
   cfg=load(pinned(request['config']))
   directory,job_tmp,host=begin_host(cfg,root/'q',request)
   with host_environment(job_tmp):
    check_host_runtime(cfg,request,host)
    cfg=stage_host(cfg,directory,request,job_tmp,stage=stage)
    check_host_scene(cfg,host)
    from rg import regenerate
    regenerate(cfg,directory)
   spec=read(kit/'k/p.json');job=os.environ.get('SLURM_JOB_ID','')
   if not job.isdigit():raise ValueError('R1_ROUTING_JOB_ID_REQUIRED')
   destination=Path(spec['n_root'])/'o'/job;destination.mkdir(parents=True,exist_ok=True,mode=0o700)
   shutil.copyfile(root/'routing_selection.json',destination/'routing_selection.json')
   r={'status':'ADMIT'}
 # d.py reads only the fully planned, authenticated configuration.
 request['_paths']=paths
 write(root.parent/'r.json',request)
 write(root.parent/'n.json',load(root/'plan.json')['config'])
 print(json.dumps({'ok':r['status']=='ADMIT'}))
 sys.exit(0 if r['status']=='ADMIT' else 1)
'''+a[end:]
 (k/'b/a.py').write_text(a)
 if (k/'b/h.py').exists():
  h=(k/'b/h.py').read_text();start=h.index("source=r/'host.json'");end=h.index("if not isinstance(host,dict)",start)
  h=h[:start]+'''hp=q.get('host_receipt')
if not isinstance(hp,dict) or set(hp)!={'path','sha256'}:raise ValueError('R1_HOST_RECEIPT_MISSING')
source=r/'q/host.json'
if hp['path']!=str(source.resolve()):raise ValueError('R1_HOST_RECEIPT_PATH_DIFFERS')
if not source.is_file() or source.is_symlink():raise ValueError('R1_HOST_RECEIPT_MISSING')
try:host=load(checked(str(source),hp['sha256']))
except (ValueError,OSError):raise ValueError('R1_HOST_RECEIPT_INVALID') from None
'''+h[end:];(k/'b/h.py').write_text(h)
 s=base64.b64decode(json.loads((k/'k/j.json').read_text())['payload']).decode()
 s=s.replace('"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/g.py"', '''if [[ "${Q_MODE:-q}" != r ]]; then
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/g.py"
fi''')
 s=s.replace('"$Q_KIT/b/a.py" q ', '"$Q_KIT/b/a.py" "${Q_MODE:-q}" ')
 s=s.replace('rc=${PIPESTATUS[0]}\n', 'rc=${PIPESTATUS[0]}\nif [[ "${Q_MODE:-q}" == r ]]; then exit "$rc"; fi\n',1)
 (k/'k/j.json').write_bytes(capsule(s.encode()))
 if (k/'b/pc.py').exists():
  p=k/'b/pc.py';s=p.read_text();s=s.replace("self.root/'r'","self.root/'p/q/r'").replace('self.root / "r"','self.root / "p/q/r"');p.write_text(s)
 print(name,reseal(k))
replace(L/'work/build24/joblib.py',(L/'work/build24/kits/n/b/z.py').read_bytes())
replace(L/'out/TREE_SEAL.json',json.dumps(dict(tree_sha256=treeh,files=len(tree)),sort_keys=True,indent=2)+'\n')
replace(L/'out/TREE_FILES.sha256',''.join(h+'  '+n+'\n' for n,h in sorted(tree.items())))
