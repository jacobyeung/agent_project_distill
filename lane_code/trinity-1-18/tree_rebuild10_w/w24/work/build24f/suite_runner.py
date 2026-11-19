from pathlib import Path
import subprocess,sys,json,os
D=Path(__file__).resolve().parent
records=[]
for name in ('suites','naming_tests','resolver_tests','launch_tests','pin_tests','refusal_tests','refresh_tests','sequence_final'):
 with (D/(name+'_24f.log')).open('w') as log:
  p=subprocess.run([sys.executable,'-I','-B',str(D/(name+'.py'))],stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'B21C_PORTABLE':'1'})
 records.append(dict(name=name,returncode=p.returncode));print(name,p.returncode,flush=True)
 (D/'VALIDATION.json').write_text(json.dumps(records,indent=2)+'\n')
