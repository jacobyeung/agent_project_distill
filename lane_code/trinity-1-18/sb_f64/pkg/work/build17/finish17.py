"""Run the remaining serialized checks and publish the bounded review package."""
from pathlib import Path
import json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build17'
suite=json.loads((B/'SUITE_RUNS.json').read_text())
assert suite['r2']['returncode']==0
records=[]
for name in ('mutations17','delta_coverage17','storage17','report17','delivery17','integrity17'):
    with (B/(name+'.log')).open('w') as output:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(B/(name+'.py'))],
                              stdout=output,stderr=subprocess.STDOUT)
    records.append(dict(script=name,returncode=result.returncode))
    (B/'FINISH.json').write_text(json.dumps(records,indent=2)+'\n')
    print(name,result.returncode,flush=True)
    if result.returncode:raise SystemExit('Stopped: inspect '+name+'.log')
