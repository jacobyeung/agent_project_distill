"""Repair the diagnosed legacy construction and restage from an empty kit root."""
import hashlib,json,subprocess,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix';T=L/'work/tree_r1'
state=json.loads((B/'QUALIFICATION.json').read_text())[-1]
assert state['status']!='running','Wait for the existing qualification process to finish normally'
assert state.get('returncode',0)>=0,'A killed process requires a user decision'
output=B/'proofs/compatibility';output.mkdir(parents=True,exist_ok=True)
prior=json.loads((B/'proofs/suite_tree/r2/results.json').read_text())
(output/'INITIAL_ERROR.json').write_text(json.dumps(dict(source_seal=json.loads((L/'out/TREE_SEAL.json').read_text())['tree_sha256'],errors=prior['errors']),indent=2)+'\n')
path=T/'student_pilot/carrier_c1_run.py';raw=path.read_text()
old='        if self.r1_training:\n';new="        if getattr(self, 'r1_training', False):\n"
assert raw.count(old)==1
before=hashlib.sha256(raw.encode()).hexdigest();path.write_text(raw.replace(old,new,1))
(B/'REQUALIFICATION.json').write_text(json.dumps(dict(pending=False,reason='Legacy reader flag defaults to false; native R1 construction still supplies the flag. Full qualification remains pending.',before_sha256=before,after_sha256=hashlib.sha256(path.read_bytes()).hexdigest()),indent=2)+'\n')
(B/'FINAL_PASS.json').write_text(json.dumps(dict(status='REQUALIFYING',GO=False))+'\n')
(B/'STATUS.md').write_text('# Build n1 status\n\nThe legacy reader compatibility fix is under qualification. GO=false. Source: work/n1fix/REQUALIFICATION.json.\n')
py=[sys.executable,'-I','-s','-B']
subprocess.run(py+[str(B/'test_runner.py'),str(output),'tests.test_r2_build8.InputReaders.test_real_materializer_rows_and_frame_loader_refusals'],check=True)
subprocess.run(py+[str(B/'seal.py')],check=True)
sys.path.insert(0,str(T))
from launch_r1.build import build
kit=B/'kits/r1';old_result=json.loads((B/'KIT_RESULT.json').read_text())
archive=B/'proofs/kit_build'/('source_'+old_result['source_seal'][:12])
assert not archive.exists();kit.rename(archive)
result=build(B/'inputs/config.json',B/'inputs',kit)
(B/'KIT_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
subprocess.run(py+[str(B/'qualify.py')],check=True)
