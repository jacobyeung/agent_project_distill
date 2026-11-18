from pathlib import Path
import json,subprocess,sys,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2'
records=[]
for name in ('proof_gate_edges9.py','proof_host_checks.py','proof_contract_closure.py','proof_registry_closure.py','mutations.py','legacy_guard_proof.py'):
    with (B/(name+'.log')).open('w') as log:
        code=subprocess.run([sys.executable,'-I','-s','-B',str(B/name)],cwd=L,stdout=log,stderr=subprocess.STDOUT).returncode
    if code<0:raise SystemExit('Proof killed; stop without retry: '+name)
    records.append(dict(script=name,sha256=hashlib.sha256((B/name).read_bytes()).hexdigest(),returncode=code))
    (B/'SUPPLEMENT_RESULTS.json').write_text(json.dumps(records,indent=2))
    print(name+': '+str(code),flush=True)
    if code:raise SystemExit(code)
