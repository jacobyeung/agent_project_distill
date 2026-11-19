"""Run archived CPU-fixture staging, public-kit pins and the real submit checker."""
import hashlib,importlib.util,json,re,subprocess,sys,tarfile,uuid
from pathlib import Path
import torch
torch.set_num_threads(8)
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out'
m=json.loads((O/'patches/MANIFEST.json').read_text());source=Path(m['verification_root'])/'src'
sys.path[:0]=[str(source),str(source/'u0'),str(O/'kit_parity50')]
from u0.a20 import gate,SUBMIT_CHECK,package_config
root=Path(re.search(r'CPU bound-export fixture: (.+)',(O/'checks/applied_round4.txt').read_text()).group(1))
target=root/'built';out=L/'work'/('gate-probe8-'+uuid.uuid4().hex);out.mkdir()
proof=target/'proof';cpu=json.loads((proof/'CPU.json').read_text());asset=cpu['gate_assets']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
archive=Path(asset['path']);assert sha(archive)==asset['sha256'] and archive.stat().st_size==asset['bytes']
assert archive.stat().st_mtime_ns <= (proof/'CPU.json').stat().st_mtime_ns
assert (proof/'1.json').read_bytes()==(target/'package/a/1.json').read_bytes()
settings=json.loads((proof/'SETTINGS.json').read_text());d=Path(settings['export_dir']).parent
# Lose access to the original namespace data, then reconstruct its logical paths from the archive.
d.rename(d.with_name('retained-data8'));d.mkdir()
with tarfile.open(archive) as t:
    assert all(not Path(x.name).is_absolute() and '..' not in Path(x.name).parts for x in t)
subprocess.run(['/bin/tar','-xf',str(archive),'-C',str(d)],check=True)
assert json.loads((d/'READY.json').read_text())==cpu['ready']
config=json.loads((O/'kit_parity50/config.example.json').read_text())
config.update(export=settings['export_dir'],artifact_manifest=settings['artifact_manifest'],export_pin=str(d/'6.json'),environment_receipt=str(d/'ENVIRONMENT.json'))
(out/'template.json').write_text(json.dumps(config))
args=(target,proof/'SETTINGS.json',proof/'CPU.json',out/'template.json',out/'settings.json',out/'config.json',proof)
config=gate(*args)
cmd=[sys.executable,'-I','-s','-B',str(source/'u0/a11.py'),'stage-kit','--source-root',str(source),
     '--input',str(O/'kit_parity50'),'--out',str(out/'u0')]
subprocess.run(cmd,check=True)
spec=importlib.util.spec_from_file_location('public_kit8',out/'u0/u0.py');kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)
kit.validate_profile(config,json.loads((out/'settings.json').read_text()));kit.validate_assets(config);kit.validate_kit(config)
assert kit.kit_hashes()==config['adoption_kit']
try:kit.validate_environment(config)
except ValueError:pass
else:raise AssertionError('CPU-only fixture environment authorized GPU execution')
print('PASS: actual CPU fixture environment refuses before synthetic GPU receipt serialization.')
for name in ('u0.py','u1.py','u0.json'):
    p=out/'u0'/name;original=p.read_bytes();p.write_bytes(original+b'\n')
    try:
        try:kit.validate_kit(config)
        except ValueError:pass
        else:raise AssertionError('Changed staged bytes accepted: '+name)
    finally:p.write_bytes(original)
package,pub,cfg=package_config(target);(package/'a/c').mkdir()
for name in ('CPU.json','MEMORY.json','ENVIRONMENT.json'):(package/'a/c'/name).write_bytes((proof/name).read_bytes())
for name in ('dry.json','dry2.json'):(package/'a'/name).write_text('{"passed":true}')
# CPU fixture has cuda=None: simulate only runtime CUDA/version imports for receipt serialization.
# This is explicitly synthetic and cannot establish production GPU parity.
from unittest.mock import patch
import types
env_record=json.loads((d/'ENVIRONMENT.json').read_text())
env_record['cuda']='12.9'
(d/'ENVIRONMENT.json').write_text(json.dumps(env_record))
(proof/'ENVIRONMENT.json').write_bytes((d/'ENVIRONMENT.json').read_bytes())
cpu['ready']['environment']=sha(d/'ENVIRONMENT.json')
(package/'a/c/ENVIRONMENT.json').write_bytes((d/'ENVIRONMENT.json').read_bytes())
(package/'a/c/CPU.json').write_text(json.dumps(cpu))
config['adoption_environment']=dict(sha256=sha(d/'ENVIRONMENT.json'),torch=env_record['versions']['torch'],transformers=env_record['versions']['transformers'],cuda='12.9')
fake_torch=types.SimpleNamespace(__version__=env_record['versions']['torch'],version=types.SimpleNamespace(cuda='12.9'))
fake_transformers=types.SimpleNamespace(__version__=env_record['versions']['transformers'])
with patch.dict(sys.modules,torch=fake_torch,transformers=fake_transformers):
    kit.write_gate_receipt(out,config,True)
(package/'a/g.json').write_bytes((out/'ue.json').read_bytes())
(out/'check.py').write_text(SUBMIT_CHECK);(out/'pool').mkdir()
cmd=[sys.executable,'-I','-s','-B',str(out/'check.py'),str(package),str(out/'pool')]
r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
print(r.stdout.strip())
with patch.dict(sys.modules,torch=fake_torch,transformers=fake_transformers):
    kit.write_gate_receipt(out,config,False)
(package/'a/g.json').write_bytes((out/'ue.json').read_bytes())
r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode!=0 and 'GPU gate differs' in r.stderr,r.stderr
print('PASS: CPU helper produced the archive before CPU.json; its recorded hash/bytes and exact a/1.json match.')
print('PASS: archive reconstructs READY-identical assets after the fixture private data path becomes unavailable.')
print('PASS: public stage-kit bytes match MANIFEST-derived pins; changed driver, comparator and sealed sample each refuse.')
print('PASS: exact CPU evidence feeds gate and full submit assertions; only reviewed step400 passes; synthetic environment evidence binds submit.')
print('PASS: failed synthetic GPU receipt refuses; no GPU evidence was measured or submitted.')
print(json.dumps(dict(archive_bytes=asset['bytes'],archive_sha256=asset['sha256'],plan=config['adoption_plan_sha256'],
    assets=config['adoption_assets'],kit=config['adoption_kit'],required_device_type=config['required_device_type'],environment=config['adoption_environment']),sort_keys=True))
