"""Run archived CPU-fixture staging, public-kit pins and the real submit checker."""
import hashlib,importlib.util,json,re,subprocess,sys,tarfile,uuid
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out'
m=json.loads((O/'patches/MANIFEST.json').read_text());source=Path(m['verification_root'])/'src'
sys.path[:0]=[str(source),str(source/'u0'),str(O/'kit_parity50')]
from u0.a20 import gate,SUBMIT_CHECK,package_config
root=Path(re.search(r'CPU step-600 fixture: (.+)',(O/'checks/applied_round4.txt').read_text()).group(1))
target=root/'built';out=L/'work'/('gate-probe7-'+uuid.uuid4().hex);out.mkdir()
proof=target/'proof';cpu=json.loads((proof/'CPU.json').read_text());asset=cpu['gate_assets']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
archive=Path(asset['path']);assert sha(archive)==asset['sha256'] and archive.stat().st_size==asset['bytes']
assert archive.stat().st_mtime_ns <= (proof/'CPU.json').stat().st_mtime_ns
assert (proof/'1.json').read_bytes()==(target/'package/a/1.json').read_bytes()
settings=json.loads((proof/'SETTINGS.json').read_text());d=Path(settings['export_dir']).parent
# Lose access to the original namespace data, then reconstruct its logical paths from the archive.
d.rename(d.with_name('retained-data7'));d.mkdir()
with tarfile.open(archive) as t:
    assert all(not Path(x.name).is_absolute() and '..' not in Path(x.name).parts for x in t)
subprocess.run(['/bin/tar','-xf',str(archive),'-C',str(d)],check=True)
assert json.loads((d/'READY.json').read_text())==cpu['ready']
config=json.loads((O/'kit_parity50/config.example.json').read_text())
config.update(export=settings['export_dir'],artifact_manifest=settings['artifact_manifest'],export_pin=str(d/'6.json'))
(out/'template.json').write_text(json.dumps(config))
args=(target,proof/'SETTINGS.json',proof/'CPU.json',out/'template.json',out/'settings.json',out/'config.json',proof)
try:gate(*args)
except ValueError as e:assert 'selected export' in str(e)
else:raise AssertionError('Default step-400 gate accepted synthetic step-600 export')
config=gate(*args,bound_export=proof/'EXPORT_PIN.json')
cmd=[sys.executable,'-I','-s','-B',str(source/'u0/a11.py'),'stage-kit','--source-root',str(source),
     '--input',str(O/'kit_parity50'),'--out',str(out/'u0')]
subprocess.run(cmd,check=True)
spec=importlib.util.spec_from_file_location('public_kit7',out/'u0/u0.py');kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)
kit.validate_profile(config,json.loads((out/'settings.json').read_text()));kit.validate_assets(config);kit.validate_kit(config)
assert kit.kit_hashes()==config['adoption_kit']
for name in ('u0.py','u1.py','u0.json'):
    p=out/'u0'/name;original=p.read_bytes();p.write_bytes(original+b'\n')
    try:
        try:kit.validate_kit(config)
        except ValueError:pass
        else:raise AssertionError('Changed staged bytes accepted: '+name)
    finally:p.write_bytes(original)
package,pub,cfg=package_config(target);(package/'a/c').mkdir()
for name in ('CPU.json','MEMORY.json'):(package/'a/c'/name).write_bytes((proof/name).read_bytes())
for name in ('dry.json','dry2.json'):(package/'a'/name).write_text('{"passed":true}')
kit.write_gate_receipt(out,config,True);(package/'a/g.json').write_bytes((out/'ue.json').read_bytes())
(out/'check.py').write_text(SUBMIT_CHECK);(out/'pool').mkdir()
cmd=[sys.executable,'-I','-s','-B',str(out/'check.py'),str(package),str(out/'pool')]
r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
print(r.stdout.strip())
kit.write_gate_receipt(out,config,False);(package/'a/g.json').write_bytes((out/'ue.json').read_bytes())
r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode!=0 and 'GPU gate differs' in r.stderr,r.stderr
print('PASS: CPU helper produced the archive before CPU.json; its recorded hash/bytes and exact a/1.json match.')
print('PASS: archive reconstructs READY-identical assets after the fixture private data path becomes unavailable.')
print('PASS: public stage-kit bytes match MANIFEST-derived pins; changed driver, comparator and sealed sample each refuse.')
print('PASS: exact CPU evidence feeds gate and full submit assertions; default400 refuses synthetic600, explicit selection passes.')
print('PASS: failed synthetic GPU receipt refuses; no GPU evidence was measured or submitted.')
print(json.dumps(dict(archive_bytes=asset['bytes'],archive_sha256=asset['sha256'],plan=config['adoption_plan_sha256'],
    assets=config['adoption_assets'],kit=config['adoption_kit'],required_device_type=config['required_device_type']),sort_keys=True))
