from pathlib import Path
import subprocess,sys,os,json
L=Path(__file__).resolve().parents[2];D=L/'work/build24c'
steps=[*(f'guard_{n}_{k}' for n in ('q','n') for k in ('new','legacy')),'kit_tests','resolver_tests','resolver23_tests','lookahead']
records=[]
for name in steps:
 with (D/(name+'.log')).open('w') as f:
  r=subprocess.run([sys.executable,'-I','-s','-B',str(D/(name+'.py'))],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'B21C_PORTABLE':'1'})
 records.append(dict(name=name,returncode=r.returncode));(D/'SUITES.json').write_text(json.dumps(records,indent=2)+'\n')
 print(name,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
