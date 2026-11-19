from pathlib import Path
import sys,subprocess,json
L=Path(__file__).resolve().parents[2];B=L/'work/build18'
records={}
for name in ('report','storage','delivery','integrity'):
    with (B/(name+'.log')).open('w') as log:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(B/(name+'18.py'))],stdout=log,stderr=subprocess.STDOUT)
    records[name]=result.returncode;print(name,result.returncode,flush=True)
    if result.returncode:raise SystemExit('Inspect '+name+' log')
(B/'FINAL_DELIVERY_RUNS.json').write_text(json.dumps(records,indent=2)+'\n')
