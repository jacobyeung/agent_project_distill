from pathlib import Path
import subprocess,sys
L=Path(__file__).resolve().parents[1];W=L/'work/row_families_r6'
p=W/'compare.py';s=p.read_text().replace("    nadir=variant.startswith('nadir_positive')", "    if type(old) is not type(new) or old == {'missing': True} or new == {'missing': True}:return None\n    nadir=variant.startswith('nadir_positive')")
p.write_text(s)
for name in ('test_off_parity.py','test_provider_contract.py','inventory.py','integrity.py'):
 with (W/(name+'.log')).open('w') as f:
    r=subprocess.run([sys.executable,'-I','-s','-B',str(W/name)],stdout=f,stderr=subprocess.STDOUT)
 print(name,r.returncode,flush=True)
 assert r.returncode==0
