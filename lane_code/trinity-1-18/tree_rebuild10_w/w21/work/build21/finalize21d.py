from pathlib import Path
import json,os,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21d'
records=json.loads((D/'SUITES.json').read_text())
assert len(records)==4 and all(x['returncode']==0 for x in records)
steps=[
    ('coverage21d',['trace21d.py','guard',str(B/'test21.py'),
        'naming_test21c.Naming21c.test_map_keys_and_relative_values']),
    ('verify',['verify_kits21.py']),
    ('scan',['scan21d.py']),
    ('metadata',['metadata21d.py']),
    ('package',['package21d.py']),
    ('report',['report21d.py']),
]
for label,args in steps:
    subprocess.run(['date','-u'],check=True)
    with (D/(label+'.log')).open('w') as f:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(B/args[0]),*args[1:]],
            stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'B21_PROOF':label})
    print(label,result.returncode,flush=True)
    if result.returncode:raise SystemExit('Check failed: '+label)
