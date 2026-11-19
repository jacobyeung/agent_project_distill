from pathlib import Path
import datetime,json,os,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23d'
steps=[('resolver',['resolver21e.Resolver21e']),('kit',['jobtest.Job20','review21.Review21']),
 ('naming21c',['naming_test21c.Naming21c']),('naming21d',['naming_test21d.Naming21d']),
 ('scanner',['naming_test21f.Naming21f','naming_test21g.Naming21g'])]
records=[]
for name,args in steps:
 with (D/(name+'.log')).open('w') as f:
  result=subprocess.run([sys.executable,'-I','-s','-B',str(D/'test_wrapper.py'),*args],
   stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'B21_PROOF':'b23d_'+name,'B21C_PORTABLE':'1'})
 proof=json.loads((B/'proofs'/('b23d_'+name)/'TESTS.json').read_text())
 records.append(dict(name=name,returncode=result.returncode,tests=proof['tests'],successful=proof['successful'],timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 (D/'SUITES.json').write_text(json.dumps(records,indent=2)+'\n')
 print(name,result.returncode,proof['tests'],flush=True)
 if result.returncode:raise SystemExit('Inspect '+name+'.log')
