from pathlib import Path
import datetime,json,os,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21g'
steps=[('scanner21g',['naming_test21f.Naming21f','naming_test21g.Naming21g']),
       ('focused',None),('resolver21g',['resolver21e.Resolver21e']),
       ('kit21g',['jobtest.Job20','review21.Review21']),
       ('naming21cg',['naming_test21c.Naming21c','review21.Review21']),
       ('extra21cg',['naming_test21c.Naming21c.test_source_map_authentication','naming_test21c.Naming21c.test_resolver_map_and_snapshot_refusals','naming_test21c.Naming21c.test_invalid_source_inventory']),
       ('naming21dg',['naming_test21d.Naming21d'])]
records=[]
for label,args in steps:
    subprocess.run(['date','-u'],check=True)
    command=[str(B/'focused.py')] if args is None else [str(B/'test21g.py'),*args]
    if label in ('scanner21g','naming21dg'):command=[str(B/'trace21g.py'),label,*command]
    with (D/(label+'.log')).open('w') as f:
        result=subprocess.run([sys.executable,'-I','-s','-B',*command],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'B21_PROOF':label})
    records.append(dict(name=label,returncode=result.returncode,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    (D/'SUITES.json').write_text(json.dumps(records,indent=2)+'\n');print(label,result.returncode,flush=True)
    if result.returncode:raise SystemExit('Check failed: '+label)
