"""Finalize reports and package only after the fixed-source qualification succeeds."""
from pathlib import Path
import json,os,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build16'
records=json.loads((B/'QUALIFICATION.json').read_text())
assert records[-1]==dict(name='storage',returncode=0),records[-1]
assert all(r['returncode']==0 or (r['name']=='packet' and r['returncode']==1) for r in records)
def run(name,script,args=(),env=None):
    with (B/(name+'.log')).open('w') as log:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(B/script),*args],
            cwd=L,env={**os.environ,**(env or {})},stdout=log,stderr=subprocess.STDOUT)
    if result.returncode<0:raise SystemExit('Process killed; stopped without retry: '+name)
    assert result.returncode==0,(name,result.returncode)
    print(name,'PASS',flush=True)
run('init_boundary','test16.py',('init_boundary_test16.InitializationBoundary',),env={'B16_PROOF':'init_boundary'})
run('coverage','coverage16.py')
run('delta_coverage','delta_coverage16.py')
run('report','report16.py')
run('delivery','delivery16.py')
run('integrity','integrity16.py')
run('storage','storage16.py')
