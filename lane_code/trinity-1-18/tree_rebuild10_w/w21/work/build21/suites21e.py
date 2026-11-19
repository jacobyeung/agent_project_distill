from pathlib import Path
import datetime,json,os,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21e'
steps=[('resolver21e',[str(B/'test21.py'),'resolver21e.Resolver21e']),
    ('focused',[str(B/'focused.py')]),
    ('kit21c',[str(B/'test21.py'),'jobtest.Job20','review21.Review21']),
    ('naming21c',[str(B/'test21.py'),'naming_test21c.Naming21c','review21.Review21']),
    ('extra21c',[str(B/'test21.py'),'naming_test21c.Naming21c.test_source_map_authentication',
        'naming_test21c.Naming21c.test_resolver_map_and_snapshot_refusals','naming_test21c.Naming21c.test_invalid_source_inventory']),
    ('naming21d',[str(B/'test21.py'),'naming_test21d.Naming21d']),
    ('coverage21d',[str(B/'test21.py'),'naming_test21c.Naming21c.test_map_keys_and_relative_values'])]
for _,args in steps:
    if args[0]==str(B/'test21.py'):args[0]=str(B/'test21e.py')
for label,args in steps:
    if label in ('resolver21e','kit21c'):args[:0]=[str(B/'trace21e.py'),label]
records=[]
for label,args in steps:
    subprocess.run(['date','-u'],check=True)
    with (D/(label+'.log')).open('w') as f:
        result=subprocess.run([sys.executable,'-I','-s','-B',*args],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'B21_PROOF':label})
    records.append(dict(name=label,returncode=result.returncode,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    (D/'SUITES.json').write_text(json.dumps(records,indent=2)+'\n');print(label,result.returncode,flush=True)
    if result.returncode:raise SystemExit('Check failed: '+label)
