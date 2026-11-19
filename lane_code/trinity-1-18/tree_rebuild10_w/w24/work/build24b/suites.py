from pathlib import Path
import os,subprocess,sys,json
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';B=L/'work/build24'
steps=[('build22',L/'work/build22/new_tests.py'),('build23',B/'tests23.py'),('build23b',B/'tests23b.py'),('resolver23',B/'resolver23_tests.py'),('resolver24',B/'resolver_tests.py'),('kit24',B/'kit_tests.py'),('regressions',B/'regressions.py')]
records=json.loads((D/'SUITES.json').read_text()) if (D/'SUITES.json').exists() else []
for name,path in steps:
 if any(x['name']==name and x['returncode']==0 for x in records):continue
 subprocess.run(['date','-u'],check=True)
 with (D/(name+'.log')).open('w') as f:
  r=subprocess.run([sys.executable,'-I','-s','-B',str(path)],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'B21C_PORTABLE':'1'})
 records=[x for x in records if x['name']!=name];records.append(dict(name=name,returncode=r.returncode));(D/'SUITES.json').write_text(json.dumps(records,indent=2)+'\n');print(name,r.returncode,flush=True)
 if r.returncode:break
