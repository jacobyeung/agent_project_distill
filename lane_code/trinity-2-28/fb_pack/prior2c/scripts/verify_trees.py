"""Derive both accepted patched tree pins from authenticated bases and PATCH_PRIOR."""
import copy,hashlib,importlib.util,json,os,shlex,shutil,subprocess,sys,tarfile
from pathlib import Path
W=Path(__file__).resolve().parents[1];FB=W.parent;sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('checker',W/'out/prove_on_prepared.py')
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
E=G.Evidence();E.track(__file__);E.track(G.__file__)
patch=E.track(FB/'prior2/out/PATCH_PRIOR.patch','b5cece7d3dc0103043e9174887b6096497eafec9e9017b3767387fa420fc0210')
E.track(FB/'prior2b/out/SEALED_PATCH.json');E.track(FB/'priorrev/work/S1_APPLY.json')
records=[]
for name,base,new in [('host',FB/'prior2b/work/sealed_base',FB/'prior2b/work/sealed_new'),
                      ('review',FB/'priorrev/work/base',FB/'priorrev/work/new')]:
 files,b=G.tree_inventory(base,E);expected,p=G.tree_inventory(new,E)
 assert G.SEALED_PAIRS[p]==b
 root=W/'work/tree_verification'/name;root.mkdir(parents=True,exist_ok=False)
 for path in files:
  dest=root/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/path,dest)
 cmd=['patch','--batch','--fuzz=0','-p1','-d',str(root),'-i',str(patch)]
 proc=subprocess.run(cmd,text=True,capture_output=True)
 (W/'work'/('patch_'+name+'.log')).write_text(proc.stdout+proc.stderr)
 rebuilt,h=G.tree_inventory(root,E)
 ok=proc.returncode==0 and rebuilt==expected and h==p
 records.append(dict(name=name,status='PASS' if ok else 'FAIL',base_tree_sha256=b,patched_tree_sha256=p,
                     base_files=len(files),patched_files=len(expected),command=shlex.join(cmd),returncode=proc.returncode))
 print(name,records[-1]['status'],p,flush=True)

# Verify the native source-seal checks in isolation using an explicitly labelled fixture.
sys.path.insert(0,str(FB/'prior2b/work/sealed_new'))
from student_pilot import p3_provenance as P,source_seal as S
P.pinned=E.pinned
from student_pilot.carrier_c1_run import identity
import torch
torch.set_num_threads(16)
root=W/'work/seal_tests';root.mkdir(exist_ok=True)
tree=FB/'prior2b/work/sealed_new';files,h=G.tree_inventory(tree,E)
archive=root/'patched_source.tar'
with tarfile.open(archive,'x') as tar:
 for name in sorted(files):tar.add(tree/name,arcname=name,recursive=False)
seal=dict(schema=S.SCHEMA,files=files,tree_sha256=h,commit='sha256:'+h,archive=E.pin(archive))
sealpin=E.write(root/'code.json',seal)
cfg=dict(scope='FIXTURE_ONLY_NOT_PRODUCTION',contract_epoch=False,code=sealpin)
receipt=dict(config_sha256=identity(cfg));receipt['source_seal']=S.binding(seal,receipt['config_sha256'])
checks=[]
def check(name,fn,error=None):
 try:fn();actual=None
 except Exception as exc:actual=type(exc).__name__+':'+str(exc)
 ok=(actual is None) if error is None else actual is not None and error in actual
 checks.append(dict(name=name,status='PASS' if ok else 'FAIL',expected_error=error,actual_error=actual))
 print(name,checks[-1]['status'],flush=True)
check('sealed_metadata_positive',lambda:G.sealed_preparation(cfg,receipt,files,h,E))
check('missing_code_seal',lambda:G.sealed_preparation({},receipt,files,h,E),'MISSING:config.code')
bad=copy.deepcopy(receipt);bad['source_seal']['tree_sha256']='0'*64
check('receipt_tree_rewritten',lambda:G.sealed_preparation(cfg,bad,files,h,E),'REAL_PREPARATION_SOURCE_SEAL_MISMATCH')
bad_config=copy.deepcopy(cfg);bad_config['scope']='changed'
check('config_identity_changed',lambda:G.sealed_preparation(bad_config,receipt,files,h,E),'REAL_PREPARATION_CONFIG_IDENTITY_MISMATCH')
bad_seal=copy.deepcopy(seal);bad_seal['tree_sha256']='0'*64
bad_cfg=dict(cfg,code=E.write(root/'bad_code.json',bad_seal))
check('config_tree_rewritten',lambda:G.sealed_preparation(bad_cfg,receipt,files,h,E),'REAL_PATCHED_SOURCE_SEAL_MISMATCH')
bad_seal=copy.deepcopy(seal);bad_seal['files']['student_pilot/p3_provenance.py']='0'*64
bad_cfg=dict(cfg,code=E.write(root/'bad_files.json',bad_seal))
check('unlisted_code_changed',lambda:G.sealed_preparation(bad_cfg,receipt,files,h,E),'REAL_PATCHED_SOURCE_SEAL_MISMATCH')
E.code([tree])
E.write(W/'out/TREE_PROVENANCE.json',dict(status='PASS' if all(r['status']=='PASS' for r in records+checks) else 'FAIL',
    records=records,seal_tests=checks,scope='Authenticated tree derivation; seal unit fixture is NONPRODUCTION.',
    command=shlex.join(sys.argv)))
raise SystemExit(0 if all(r['status']=='PASS' for r in records+checks) else 1)
