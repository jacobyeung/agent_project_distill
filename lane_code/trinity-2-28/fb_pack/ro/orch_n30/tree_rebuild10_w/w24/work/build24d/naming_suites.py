from pathlib import Path
import subprocess,sys,os,json
L=Path(__file__).resolve().parents[2];D=L/'work/build24d';B=L/'work/build21'
steps=[('scanner',['naming_test21f.Naming21f','naming_test21g.Naming21g']),('resolver',['resolver21e.Resolver21e']),('kit',['jobtest.Job20','review21.Review21']),('naming21c',['naming_test21c.Naming21c']),('naming21d',['naming_test21d.Naming21d'])]
records=[]
for name,args in steps:
 with (D/('regression_'+name+'.log')).open('w') as f:
  p=subprocess.run([sys.executable,'-I','-s','-B',str(B/'test21g.py'),*args],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'B21C_PORTABLE':'1','B21_PROOF':'build24c_'+name,'B22_ROOM_FIXTURE':str(L/'work/build24/proofs/capacity/600/request_config.json')})
 records.append(dict(name=name,returncode=p.returncode));(D/'REGRESSIONS.json').write_text(json.dumps(records,indent=2)+'\n')
 print(name,p.returncode,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
