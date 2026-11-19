from pathlib import Path
import json,subprocess,sys,os
D=Path(__file__).resolve().parent
records=[]
for name in ('suites','naming_tests','resolver_tests'):
    with (D/(name+'.log')).open('w') as log:
        p=subprocess.run([sys.executable,'-I','-s','-B',str(D/(name+'.py'))],stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'B21C_PORTABLE':'1'})
    records.append(dict(name=name,returncode=p.returncode))
    (D/'VALIDATION.json').write_text(json.dumps(records,indent=2)+'\n')
    print(name,p.returncode,flush=True)
    if p.returncode:raise SystemExit(p.returncode)
