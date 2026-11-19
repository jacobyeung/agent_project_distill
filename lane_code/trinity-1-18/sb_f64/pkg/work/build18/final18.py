"""Run the final source checks serially, retaining every result."""
from pathlib import Path
import subprocess,sys,json,os
L=Path(__file__).resolve().parents[2];B=L/'work/build18'
steps=[('final_checks',[B/'final_checks18.py']),('real',[B/'real18.py']),
       ('seal',[L/'work/n1fix2/seal.py']),('kits',[B/'kits18.py']),
       ('packet_inputs',[B/'packet_inputs18.py']),('suite',[B/'suite18.py']),
       ('packet',[B/'packet18.py','tree','final18','packet']),('coverage',[B/'delta_coverage18.py']),
       ('storage',[B/'storage18.py'])]
records={}
for name,args in steps:
    with (B/(name+'.log')).open('w') as log:
        result=subprocess.run([sys.executable,'-I','-s','-B',*map(str,args)],stdout=log,stderr=subprocess.STDOUT,env=os.environ)
    records[name]=result.returncode;(B/'FINAL_RUNS.json').write_text(json.dumps(records,indent=2))
    print(name,result.returncode,flush=True)
    if name=='packet':
        with (B/'regressions.log').open('w') as log:
            comparison=subprocess.run([sys.executable,'-I','-s','-B',str(B/'compare18.py')],stdout=log,stderr=subprocess.STDOUT,env=os.environ)
        if comparison.returncode:raise SystemExit('Inspect regression comparison')
    elif result.returncode:raise SystemExit('Inspect retained failure: '+name)
