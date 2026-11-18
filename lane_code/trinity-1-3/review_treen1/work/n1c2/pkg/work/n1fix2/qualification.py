"""Run local proof phases sequentially with fixed outputs and explicit failure stops."""
from pathlib import Path
import json,subprocess,sys,os,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2'
def run(name,args,allow_failure=False):
    (B/'STATUS.md').write_text('Build n1fix2: '+name+' is running. GO=false. All implementation fixes are present; qualification is pending. See '+name+'.log and proofs/.\n')
    with (B/(name+'.log')).open('w') as log:
        code=subprocess.run(args,cwd=L,stdout=log,stderr=subprocess.STDOUT).returncode
    if code<0:raise SystemExit('A process was killed; stop without retry: '+name)
    if code and not allow_failure:raise SystemExit(name+' failed: '+str(code))
    print(name+': '+str(code),flush=True)
py=[sys.executable,'-I','-s','-B']
for name,args in [
 ('targeted',py+[str(B/'test_runner.py'),str(B/'proofs/targeted'),'tests.test_r2_n1fix','tests.test_r2_n1fix2','tests.test_r2_build_n1']),
 ('text',py+[str(B/'proof_text.py')]),
 ('forward',py+[str(B/'proof_forward9.py')]),
 ('packet',['bash',str(B/'PACKET_TEST.sh')]),
 ('seal',py+[str(B/'seal.py')]),
 ('kits',py+[str(B/'stage9.py')]),
 ('delivery',py+[str(B/'make_delivery.py')])]:run(name,args)
delivery=json.loads((B/'DELIVERY.json').read_text())
run('package',['bash',str(B/'PACKAGE_TEST.sh'),str(L/delivery['path'])],allow_failure=True)
(B/'STATUS.md').write_text('Proof phases and frozen suite have finished. Coverage, regression comparison and final report are pending. GO=false.\n')
