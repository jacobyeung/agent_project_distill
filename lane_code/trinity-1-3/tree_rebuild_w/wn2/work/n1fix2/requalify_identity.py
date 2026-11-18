"""Qualify the final target identity with exact snapshot receipts."""
from pathlib import Path
import json,subprocess,sys,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2'
assert (B/'proofs/package/ARCHIVE.json').is_file(),'Allow the running frozen suite to finish before requalification'
for name in ('kits','proofs/package','proofs/suite_tree'):
    p=B/name;dest=B/(name+'_identity_input')
    assert not dest.exists();p.rename(dest)
for name in ('input','store'):
    p=B/'proofs/forward'/name
    if p.exists():p.rename(p.with_name('retained_identity_'+name))
p=B/'proofs/checkpoint/producer/checkpoint'
if p.exists():p.rename(p.with_name('retained_checkpoint'))
py=[sys.executable,'-I','-s','-B']
def run(name,args):
    (B/'STATUS.md').write_text('Build n1fix2: '+name+' is running for the final target-identity source. GO=false.\n')
    with (B/(name+'.log')).open('w') as log:code=subprocess.run(args,cwd=L,stdout=log,stderr=subprocess.STDOUT).returncode
    if code<0:raise SystemExit('Process killed; stop without retry: '+name)
    print(name+': '+str(code),flush=True)
    if code:raise SystemExit(code)
for script in ('proof_target_prepared.py','proof_contract_closure.py','proof_registry_closure.py','mutations.py','proof_checkpoint.py','proof_forward9.py'):
    if script=='proof_target_prepared.py' and (B/'proofs/target_prepared/RESULT.json').exists():
        sys.path.insert(0,str(L/'work/tree_r1'))
        from student_pilot.source_seal import inventory
        from student_pilot.p3_provenance import digest
        prior=json.loads((B/'proofs/target_prepared/RESULT.json').read_text())
        if (prior.get('status')=='PASS' and prior.get('source_seal')==digest(inventory(L/'work/tree_r1'))
                and prior.get('harness_sha256')==hashlib.sha256((B/script).read_bytes()).hexdigest()):
            print('Resumed prepared-target proof with exact source and harness hashes',flush=True)
            continue
    run(script,py+[str(B/script)])
run('targeted',py+[str(B/'test_runner.py'),str(B/'proofs/targeted'),'tests.test_r2_n1fix','tests.test_r2_n1fix2','tests.test_r2_build_n1'])
run('packet',['bash',str(B/'PACKET_TEST.sh')])
run('seal',py+[str(B/'seal.py')])
run('kits',py+[str(B/'stage9.py')])
run('delivery',py+[str(B/'make_delivery.py')])
d=json.loads((B/'DELIVERY.json').read_text())
run('package',['bash',str(B/'PACKAGE_TEST.sh'),str(L/d['path'])])
