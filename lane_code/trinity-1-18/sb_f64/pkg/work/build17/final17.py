from pathlib import Path
import subprocess,sys,json,os
L=Path(__file__).resolve().parents[2];B=L/'work/build17'
steps=[
 ('mutations',[str(B/'mutations17.py')]),
 ('focused',[str(B/'test17.py'),'tests.test_r1_build17','tests.test_r1_build16','tests.test_r1_build15']),
 ('seal',[str(L/'work/n1fix2/seal.py')]),
 ('kits',[str(B/'kits17.py')]),
 ('operator',[str(B/'operator17.py')]),
 ('packet_inputs',[str(B/'packet_inputs17.py')]),
 ('suite',[str(B/'suite17.py')]),
 ('packet',[str(B/'packet17.py'),'tree','final17','packet']),
 ('coverage',[str(B/'delta_coverage17.py')]),
 ('storage',[str(B/'storage17.py')]),
]
records={}
for name,args in steps:
    with (B/(name+'.log')).open('w') as log:
        result=subprocess.run([sys.executable,'-I','-s','-B',*args],stdout=log,stderr=subprocess.STDOUT,env=os.environ)
    records[name]=result.returncode
    (B/'FINAL_RUNS.json').write_text(json.dumps(records,indent=2))
    print(name,result.returncode,flush=True)
    if result.returncode:raise SystemExit('Final check stopped at '+name+'; inspect log before further work')
