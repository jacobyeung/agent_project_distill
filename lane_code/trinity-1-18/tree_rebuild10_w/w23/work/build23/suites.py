from pathlib import Path
import datetime,json,os,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23'
steps=[('focused',None),('resolver',['resolver21e.Resolver21e']),
       ('kit',['jobtest.Job20','review21.Review21']),
       ('naming21c',['naming_test21c.Naming21c']),
       ('naming21d',['naming_test21d.Naming21d']),
       ('scanner',['naming_test21f.Naming21f','naming_test21g.Naming21g'])]
start=sys.argv[1] if len(sys.argv)>1 else None
records=[r for r in json.loads((D/'SUITES.json').read_text()) if r['returncode']==0] if start else []
if start:
    first=next(i for i,(name,_) in enumerate(steps) if name==start)
    records=[r for r in records if r['name'] in {name for name,_ in steps[:first]}]
    steps=steps[first:]
for name,args in steps:
    subprocess.run(['date','-u'],check=True)
    command=[sys.executable,'-I','-s','-B',str(B/'focused.py')] if args is None else [sys.executable,'-I','-s','-B',str(B/'test21g.py'),*args]
    with (D/(name+'.log')).open('w') as f:
        result=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'B21_PROOF':'b23_'+name,'B21C_PORTABLE':'1'})
    records.append(dict(name=name,returncode=result.returncode,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    (D/'SUITES.json').write_text(json.dumps(records,indent=2)+'\n')
    print(name,result.returncode,flush=True)
    if result.returncode:raise SystemExit('Inspect '+name+'.log')
