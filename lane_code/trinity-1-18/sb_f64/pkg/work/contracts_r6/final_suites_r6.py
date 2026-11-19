from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,sys,json
L=Path(__file__).resolve().parents[1]
def run(tag,tree):
    log=L/f'work/{tag}.log'
    with log.open('w') as f:
        p=subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/run_tests_r6.py'),tree,tag,'contract'],stdout=f,stderr=subprocess.STDOUT)
    print(tag,p.returncode,flush=True)
    return dict(returncode=p.returncode,tree=tree,log=str(log),results=str(L/f'work/{tag}_results.json'),trace=str(L/f'work/{tag}_trace.json'))
with ThreadPoolExecutor(max_workers=2) as pool:
    jobs={key:pool.submit(run,tag,tree) for key,tag,tree in [('base','R6_FINAL_BASE','r6_applied'),('tree_r1','R6_FINAL_R1','r6_snapshot')]}
    results={key:f.result() for key,f in jobs.items()}
(L/'work/final_suites_r6.json').write_text(json.dumps(results,indent=2))
