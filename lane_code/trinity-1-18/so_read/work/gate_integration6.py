"""Exercise the gate and submit checker with the actual A4 CPU fixture proof."""
import hashlib,importlib.util,json,re,subprocess,sys,uuid
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out'
m=json.loads((O/'patches/MANIFEST.json').read_text());source=Path(m['verification_root'])/'src'
sys.path[:0]=[str(source),str(source/'u0'),str(O/'kit_parity50')]
from u0.a20 import gate,SUBMIT_CHECK,package_config
root=Path(re.search(r'CPU step-600 fixture: (.+)',(O/'checks/applied_round4.txt').read_text()).group(1))
target=root/'built';out=L/'work'/('gate-probe6-'+uuid.uuid4().hex);out.mkdir()
proof=target/'proof';cpu=json.loads((proof/'CPU.json').read_text())
config=json.loads((O/'kit_parity50/config.example.json').read_text())
settings=json.loads((proof/'SETTINGS.json').read_text())
config.update(export=settings['export_dir'],artifact_manifest=settings['artifact_manifest'],
              export_pin=str(Path(settings['export_dir']).parent/'6.json'))
(out/'template.json').write_text(json.dumps(config))
config=gate(target,proof/'SETTINGS.json',proof/'CPU.json',out/'template.json',out/'settings.json',out/'config.json',proof)
spec=importlib.util.spec_from_file_location('gate_kit6',O/'kit_parity50/run.py');kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)
kit.validate_profile(config,json.loads((out/'settings.json').read_text()))
kit.validate_assets(config)
for name,key in [('RESTORE.json','restore'),('binding.json','binding')]:
    assert hashlib.sha256((proof/name).read_bytes()).hexdigest()==cpu['ready'][key]
# Exercise receipt serialization and CPU preflight only; this is synthetic GPU evidence.
package,pub,cfg=package_config(target);(package/'a/c').mkdir()
for name in ('CPU.json','MEMORY.json'):(package/'a/c'/name).write_bytes((proof/name).read_bytes())
for name in ('dry.json','dry2.json'):(package/'a'/name).write_text('{"passed":true}')
kit.write_gate_receipt(out,config,True);(package/'a/g.json').write_bytes((out/'ue.json').read_bytes())
(out/'check.py').write_text(SUBMIT_CHECK);(out/'pool').mkdir()
cmd=[sys.executable,'-I','-s','-B',str(out/'check.py'),str(package),str(out/'pool')]
result=subprocess.run(cmd,capture_output=True,text=True);assert result.returncode==0,result.stderr
print(result.stdout.strip())
kit.write_gate_receipt(out,config,False);(package/'a/g.json').write_bytes((out/'ue.json').read_bytes())
result=subprocess.run(cmd,capture_output=True,text=True);assert result.returncode!=0 and 'GPU gate differs' in result.stderr,result.stderr
print('PASS: exact CPU-emitted restore/binding/export receipts feed the gate; staged bytes and manifest recheck.')
print('PASS: real bundle/entry/memory CPU proof passes cont_ops assertions; synthetic failed GPU receipt refuses.')
print('No GPU evidence was measured: receipt serialization used explicit synthetic pass/fail controls.')
print(json.dumps(dict(plan=config['adoption_plan_sha256'],assets=config['adoption_assets'],required_device_type=config['required_device_type']),sort_keys=True))
