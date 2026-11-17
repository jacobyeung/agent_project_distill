"""Refresh native export/reload coverage without changing the sealed source."""
import json,os,subprocess,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build8';P=B/'proofs/export_refresh'
if any(r['status']=='running' for r in json.loads((B/'FINAL_PASS.json').read_text())):
 raise SystemExit('The final pass must finish before another proof uses temporary storage')
env={**os.environ,'R2_TREE':str(L/'work/tree_r1'),'R2_LANE_ROOT':str(L),
     'R2_ALL_TESTS':'0','R2_SUITE_GROUP':'','R2_PACKAGE_MEMBERS':''}
py=[sys.executable,'-I','-s','-B']
with (B/'export_refresh.log').open('w') as log:
 result=subprocess.run(py+[str(B/'test_runner.py'),str(P),
  'tests.test_r2_build7.InputTests.test_real_export_manifest_and_reader'],
  env=env,cwd=L,stdout=log,stderr=subprocess.STDOUT)
if result.returncode<0:raise SystemExit('Export proof was killed; stop without retry')
if result.returncode:raise SystemExit('Export proof failed; inspect export_refresh.log')
evidence=dict(test='tests.test_r2_build7.InputTests.test_real_export_manifest_and_reader',
 real_functions=['carrier_c1_run.export','b7_inputs.module_trainability','eat1_export.write_manifest',
                 'carrier_c1_run.load_artifact','CarrierC1.probe'],
 stand_ins=['tiny pretrained LM and auxiliary-head weights','single CPU rank at the distributed/FSDP state-collection boundary'],
 reason='The existing suite test reuses a persistent artifact when present. Its refreshed receipt therefore omitted the publication branch. This dedicated fixed proof folder executes the unchanged producer and reader from a fresh artifact.',
 source_changed=False)
(P/'SOURCE.json').write_text(json.dumps(evidence,indent=2)+'\n')
subprocess.run(py+[str(B/'coverage_all.py')],env=env,cwd=L,check=True)
if json.loads((B/'GAPS.json').read_text()):raise SystemExit('CPU gaps remain after export proof')
with (B/'STATUS.md').open('a') as f:
 f.write('\nThe unchanged native export/reload test passed in its dedicated fixed proof folder; coverage has zero CPU gaps (`proofs/export_refresh/results.json`, `proofs/export_refresh/SOURCE.json`, `GAPS.json`). The sealed tree and archive were unchanged.\n')
