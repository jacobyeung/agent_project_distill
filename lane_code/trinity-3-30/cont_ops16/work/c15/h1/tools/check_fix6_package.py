"""Rebuild deterministic packet outputs and compare a fresh derived fixture."""
import ast,hashlib,json,os,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parents[1];sys.path.insert(0,str(H/'tools'))
import derive_kit_h1 as dk
out=H/'evidence/fix6_package';out.mkdir()
sha=dk.sha
names=['tools/derive_kit_h1.py','runtime/jb.sh','ids.json','TOKENS_H1.json','UPLOAD.json','orch_h1.sh','fin_h1.sh','build/c_patch.sh']+[str(p.relative_to(H)) for p in (H/'payload').iterdir() if p.is_file()]
before={n:sha(H/n) for n in names}
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
for tool in ('make_deriver','make_runtime','make_orchard','build_config_patch'):
 subprocess.run([sys.executable,'-B',str(H/'tools'/(tool+'.py'))],env=env,check=True)
assert before=={n:sha(H/n) for n in names},'nondeterministic rebuild'
# Full fixture comparison preserves absent source pins and all modes.
over=json.loads((H/'build/over_fx.json').read_text())
result=dk.derive('/scratch/jjyeung/orch_n30/review_h1pkt/work/d0/kitfull',out/'fx',over)
assert result==json.loads((H/'evidence/fx.json').read_text())
assert (out/'fx/SHA256SUMS.txt').read_bytes()==(H/'build/fx/SHA256SUMS.txt').read_bytes()
members=dk.manifest_members(H/'build/fx')
missing=set(result['absent_source_files'])
assert len(missing)==2
for n in (set(members)-missing)|dk.member_directories(members):
 assert (out/'fx'/n).lstat().st_mode==(H/'build/fx'/n).lstat().st_mode
# The login planner executes with only the system stdlib, without torch installed/imported.
code='''import importlib.util,json,sys
from pathlib import Path
h=Path(sys.argv[1]);spec=importlib.util.spec_from_file_location('dk',h/'payload/d.py');dk=importlib.util.module_from_spec(spec);spec.loader.exec_module(dk)
cfg=json.loads((h/'evidence/fix6_before/config.json').read_text());over=json.loads((h/'build/over_fx.json').read_text())
dk.refresh_disk_plan(cfg,over)
assert cfg['checkpoint_disk_guard']['planned_weight_exports']==3 and 'torch' not in sys.modules
'''
subprocess.run(['/usr/bin/python3','-I','-B','-c',code,str(H)],check=True,env=env)
for p in [*(H/'tools').glob('*.py'),*(H/'tests').rglob('*.py'),*(H/'payload').glob('*.py')]:ast.parse(p.read_text(),filename=str(p))
for p in [*(H/'payload').glob('*.sh'),H/'runtime/jb.sh',H/'orch_h1.sh',H/'fin_h1.sh',H/'build/c_patch.sh',H/'tests/RERUN_CHAIN.sh']:subprocess.run(['/bin/bash','-n',str(p)],check=True)
assert sha(H/'tests/RERUN_CHAIN.sh')==json.loads((H/'evidence/fix6_before/hashes.json').read_text())['tests/RERUN_CHAIN.sh']
u=json.loads((H/'UPLOAD.json').read_text());assert sha(H/'build'/u['archive'])==u['sha256']
for item in u['files']:assert sha(H/'payload'/item['name'])==item['sha256']
assert u['bytes']<20_000_000 and u['script_bytes']<20_000_000
r=dict(status='PASS',deterministic=before,fixture=result,stdlib_planner='PASS',syntax='PASS',runner_unchanged=True,upload=u['sha256'])
(out/'results.json').write_text(json.dumps(r,indent=2)+'\n');print('Deterministic packet, fixture, stdlib planner and syntax PASS')
