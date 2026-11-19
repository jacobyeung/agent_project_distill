"""Run the inherited scanner and resolver suites against their authenticated kit."""
from pathlib import Path
import datetime,json,os,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build24'
steps=[('scanner',['naming_test21f.Naming21f','naming_test21g.Naming21g']),
       ('resolver',['resolver21e.Resolver21e']),
       ('kit',['jobtest.Job20','review21.Review21']),
       ('naming21c',['naming_test21c.Naming21c']),
       ('naming21d',['naming_test21d.Naming21d'])]
records=[]
for label,args in steps:
    if any(r['name']==label and r['returncode']==0 for r in records):continue
    subprocess.run(['date','-u'],check=True)
    with (D/('regression_'+label+'.log')).open('w') as f:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(B/'test21g.py'),*args],stdout=f,stderr=subprocess.STDOUT,
            env={**os.environ,'B21C_PORTABLE':'1','B21_PROOF':'build24_'+label,
                 'B22_ROOM_FIXTURE':str(D/'proofs/capacity/600/request_config.json')})
    records=[r for r in records if r['name']!=label]
    records.append(dict(name=label,returncode=result.returncode,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    (D/'REGRESSIONS.json').write_text(json.dumps(records,indent=2)+'\n');print(label,result.returncode,flush=True)
    if result.returncode:raise SystemExit('Check failed: '+label)
