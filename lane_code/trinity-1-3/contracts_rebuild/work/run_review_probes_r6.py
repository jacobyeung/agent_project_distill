from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,sys,json
L=Path(__file__).resolve().parents[1];W=L/'work/review_c5_inputs';T=L/'work/trees/r6_applied'
(W/'tmp').mkdir(exist_ok=True)
for p in W.glob('*.py'):
 p.write_text(p.read_text().replace('/scratch/jjyeung/orch_n30/review_c5/work/tmp',str(W/'tmp')))
names=['h2_frozen_basis.py','h1_live_ambient.py','h2_mixed.py','m1_binding.py','r5_probe.py']
def run(name):
 cmd=[sys.executable,'-I','-s','-B',str(W/name),str(T)]
 if name=='h2_mixed.py':cmd.append(str(W/'h2_mixed_r6.json'))
 p=subprocess.run(cmd,capture_output=True,text=True)
 log=W/(name+'.log');log.write_text(p.stdout+p.stderr)
 assert p.returncode==0,(name,p.stderr)
 if name=='m1_binding.py':assert 'DISAGREE' not in p.stdout
 if name=='h1_live_ambient.py':assert 'ERR' not in p.stdout
 if name=='r5_probe.py':assert 'disagreements 0' in p.stdout
 return name,dict(command=cmd,returncode=p.returncode,log=str(log))
with ThreadPoolExecutor(max_workers=2) as pool:results=dict(pool.map(run,names))
with (L/'out/REVIEW_C5_PROBES_R6.json').open('x') as f:json.dump(results,f,indent=2)
print('Reviewer probes passed.')
