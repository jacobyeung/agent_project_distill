"""Serialize final qualification; retain all artifacts and stop on a killed process."""
from pathlib import Path
import json, os, subprocess, sys
L=Path(__file__).resolve().parents[2]; B=L/'work/build16'
records=[]
def run(name,script,args=(),allowed=(0,),env=None):
    with (B/(name+'.log')).open('w') as log:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(script),*args],
            cwd=L,env={**os.environ,**(env or {})},stdout=log,stderr=subprocess.STDOUT)
    records.append(dict(name=name,returncode=result.returncode))
    (B/'QUALIFICATION.json').write_text(json.dumps(records,indent=2)+'\n')
    if result.returncode<0:raise SystemExit('Process killed; stopped without retry: '+name)
    if result.returncode not in allowed:raise SystemExit('Qualification failure: '+name)
    print(name,result.returncode,flush=True)
run('seal',L/'work/n1fix2/seal.py')
if (B/'kits').exists():
    (B/'kits').rename(B/'retained_kits_attempt/before_final_binding')
run('kits',B/'kits16.py')
run('mutations',B/'mutations16.py')
run('packet',B/'packet16.py',('tree','b16'),allowed=(0,1))
run('suite',B/'suite16.py')
run('final_focused',B/'test16.py',('tests.test_r1_build16','tests.test_r1_build15',
    'tests.test_r1_build14','tests.test_r2_build_n1','tests.test_r2_n1fix','tests.test_r2_n1fix3',
    'tests.test_r2_build12','tests.test_r1_build13','tests.test_r2_build3.Build3.test_opener_export_keep_and_reset'),
    env={'B16_PROOF':'final_focused'})
run('edges',B/'test16.py',('edge_test16.Edges','stage_test16.Staging'),env={'B16_PROOF':'edges'})
run('preserve',B/'preserve16.py')
run('operator',B/'operator16.py')
run('coverage',B/'coverage16.py')
run('delta_coverage',B/'delta_coverage16.py')
run('storage',B/'storage16.py')
