"""Feed the real applied A4 CPU proof's prepared bytes into the adoption gate."""
import importlib.util,json,re,sys
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out'
m=json.loads((O/'patches/MANIFEST.json').read_text());source=Path(m['verification_root'])/'src'
sys.path[:0]=[str(source),str(source/'u0')]
from u0.a20 import gate
text=(O/'checks/applied_round4.txt').read_text()
root=Path(re.search(r'CPU step-600 fixture: (.+)',text).group(1));target=root/'built'
out=L/'work/gate-probe5';out.mkdir()
config=gate(target,target/'proof/SETTINGS.json',target/'proof/CPU.json',O/'kit_parity50/config.example.json',out/'settings.json',out/'config.json')
spec=importlib.util.spec_from_file_location('real_gate5',O/'kit_parity50/run.py');kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)
kit.validate_profile(config,json.loads((out/'settings.json').read_text()))
print('PASS: real applied A4 a/5.py CPU proof and exact prepare SETTINGS.json feed the adopted GPU profile.')
print(json.dumps(dict(plan=config['adoption_plan_sha256'],enable_caches=config['enable_caches'],read_cache_bytes=config['read_cache_bytes']),sort_keys=True))
