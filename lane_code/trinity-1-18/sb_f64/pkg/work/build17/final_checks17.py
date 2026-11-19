"""Serialize the remaining frozen-source checks."""
from pathlib import Path
import os,sys,subprocess,json
L=Path(__file__).resolve().parents[2];B=L/'work/build17'
steps=[
 ('final_focused',B/'test17.py',['tests.test_r1_build17','tests.test_r1_export17',
  'tests.test_r1_build16','tests.test_r1_build15','tests.test_r1_build14','tests.test_r2_build_n1',
  'tests.test_r2_n1fix','tests.test_r2_n1fix3','tests.test_r2_build12','tests.test_r1_build13',
  'tests.test_r2_build3.Build3.test_opener_export_keep_and_reset','export_mutation17.HashTwin.test_same_size_shard_refuses']),
 ('edges',B/'test17.py',['edge_test16.Edges','stage_test16.Staging']),
 ('preservation',B/'preserve17.py',[]),
 ('coverage',B/'delta_coverage17.py',[]),
 ('storage',B/'storage17.py',[])]
records=[]
for name,script,args in steps:
    with (B/(name+'.log')).open('w') as f:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(script),*args],
            env={**os.environ,'B17_PROOF':name},stdout=f,stderr=subprocess.STDOUT)
    records.append(dict(name=name,returncode=result.returncode))
    (B/'FINAL_CHECKS.json').write_text(json.dumps(records,indent=2)+'\n')
    print(name,result.returncode,flush=True)
    if result.returncode:raise SystemExit('Check failed; inspect retained log: '+name)
