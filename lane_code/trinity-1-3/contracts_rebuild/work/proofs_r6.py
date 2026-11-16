from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,sys,os,json
L=Path(__file__).resolve().parents[1];P=sys.executable

def run(name,args,env=None):
    log=L/f'work/{name}.log'
    with log.open('w') as f:
        r=subprocess.run([P,'-I','-s','-B',*map(str,args)],stdout=f,stderr=subprocess.STDOUT,env=env)
    print(name,r.returncode,flush=True)
    return dict(returncode=r.returncode,log=str(log))
with ThreadPoolExecutor(max_workers=4) as pool:
    jobs={
    'base':pool.submit(run,'suite_base_r6',[L/'work/run_tests_r6.py','r6_applied','R6_FULL_BASE','contract']),
    'tree_r1':pool.submit(run,'suite_r1_r6',[L/'work/run_tests_r6.py','r6_snapshot','R6_FULL_R1','contract']),
    'regression':pool.submit(run,'regression_r5_r6',[L/'work/run_tests_r6.py','r5_applied','R6_OLD','tree',L/'work/tests_r6/test_review_c5.py'],dict(os.environ,R6_COMPARE=str(L/'work/row_families_r5/heading_compare.py'))),
    'audit':pool.submit(run,'real_audit_r6',[L/'work/real_audit_r6.py'])}
    results={k:f.result() for k,f in jobs.items()}
(L/'work/proof_jobs_r6.json').write_text(json.dumps(results,indent=2))
