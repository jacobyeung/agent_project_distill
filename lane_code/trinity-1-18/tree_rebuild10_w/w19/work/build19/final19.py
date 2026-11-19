"""Run the frozen-source checks serially and retain failures for inspection."""
from pathlib import Path
import sys,subprocess,os,json
L=Path(__file__).resolve().parents[2];B=L/'work/build19'
steps=[('final_checks',[B/'final_checks19.py']),('real',[B/'real19.py']),('seal',[L/'work/n1fix2/seal.py']),
       ('kits',[B/'kits19.py']),('packet_inputs',[B/'packet_inputs19.py']),('suite',[B/'suite19.py']),
       ('packet',[B/'packet19.py','tree','final19','packet']),('compare',[B/'compare19.py']),
       ('coverage',[B/'delta_coverage19.py']),('storage',[B/'storage19.py'])]
records={}
for name,args in steps:
    with (B/(name+'.log')).open('w') as log:
        r=subprocess.run([sys.executable,'-I','-s','-B',*map(str,args)],stdout=log,stderr=subprocess.STDOUT,env=os.environ)
    records[name]=r.returncode;(B/'FINAL_RUNS.json').write_text(json.dumps(records,indent=2))
    print(name,r.returncode,flush=True)
    if r.returncode and name!='packet':raise SystemExit('Inspect '+name)
