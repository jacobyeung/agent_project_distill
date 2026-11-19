from pathlib import Path
import json,subprocess,sys
B=Path(__file__).resolve().parent
p=B/'proofs/integrity/NONREGULAR.json';rows=json.loads(p.read_text())
if isinstance(rows,list):p.write_text(json.dumps(dict(archive=json.loads((B/'DELIVERY.json').read_text()),nonregular=rows),indent=2)+'\n')
records={}
for name in ('delivery','integrity'):
    with (B/(name+'.log')).open('w') as log:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(B/(name+'18.py'))],stdout=log,stderr=subprocess.STDOUT)
    records[name]=result.returncode;print(name,result.returncode,flush=True)
    if result.returncode:raise SystemExit('Inspect '+name+' log')
(B/'FINAL_DELIVERY_RUNS.json').write_text(json.dumps(dict(report=0,storage=0,**records),indent=2)+'\n')
