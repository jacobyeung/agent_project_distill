from pathlib import Path
import json, subprocess, sys, os
D=Path(__file__).resolve().parent
records=[]
for name in ('guard_q_legacy','guard_q_new','guard_n_legacy','guard_n_new','kit_tests','naming_tests','resolver_tests','resolver600_tests','resolver23_tests','live_tests','review_tests','security_tests'):
    with (D/(name+'.log')).open('w') as log:
        p=subprocess.run([sys.executable,'-I','-s','-B',str(D/(name+'.py'))],stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'B21C_PORTABLE':'1'})
    records.append(dict(name=name,returncode=p.returncode))
    (D/'SUITES.json').write_text(json.dumps(records,indent=2)+'\n')
    print(name,p.returncode,flush=True)
    if p.returncode:print((D/(name+'.log')).read_text()[-4000:],flush=True)
