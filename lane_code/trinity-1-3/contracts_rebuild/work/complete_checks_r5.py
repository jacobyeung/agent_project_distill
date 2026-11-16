from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import shutil,subprocess,sys,json
L=Path(__file__).resolve().parents[1];P=sys.executable
def run(script,args,log):
    with (L/'work'/log).open('w') as stream:
        result=subprocess.run([P,'-I','-s','-B',str(L/'work'/script),*map(str,args)],stdout=stream,stderr=subprocess.STDOUT)
    assert result.returncode==0,(script,log,result.returncode)
    print(log,'PASS',flush=True)
s=(L/'work/apply_proof_r5.py').read_text().replace('r5_proof','r5_complete_proof').replace('r5_snapshot','r5_complete_snapshot')
(L/'work/apply_complete_r5.py').write_text(s)
p=L/'work/trees/r5_complete_proof/base';p.parent.mkdir(exist_ok=True);shutil.copytree(L/'work/base/work/base/tree_b01ce449',p)
for f in [p,*p.rglob('*')]:f.chmod(f.stat().st_mode & ~0o222)
run('build_packet_r5.py',[],'packet_complete_r5.log');run('apply_complete_r5.py',[],'apply_complete_r5.log')
s=(L/'work/mutation_r5/run_close.py').read_text().replace('round_close','round_extra').replace('MUTATION_CLOSE_','MUTATION_EXTRA_')
s=s.replace("mutants += [\n ('F_GROUND", "mutants += [\n ('F_MATERIALIZER','student_pilot/s1_routing.py','entry = candidate_binding(row, manifest=contract_manifest)',\"entry = contract_manifest[str(row['qid'])]\"),\n ('F_GROUND")
s=s.replace("selectors.update({", "selectors.update({\n 'F_MATERIALIZER':'manifest_superset',")
(L/'work/mutation_r5/run_extra.py').write_text(s)
with ThreadPoolExecutor(max_workers=4) as pool:
    futures=[pool.submit(run,'run_tests_r5.py',[tree,tag,'contract'],log) for tree,tag,log in (
        ('r5_complete_proof/base','B8_COMPLETE_R5','tests_complete_r5.log'),
        ('r5_complete_snapshot','B8_COMPLETE_SNAPSHOT_R5','tests_complete_snapshot_r5.log'))]
    futures.append(pool.submit(run,'run_tests_r5.py',['r5_complete_proof/base','B8_COMPLETE_COVERAGE_R5','tree',L/'work/coverage_probes_r5.py'],'coverage_complete_r5.log'))
    futures.append(pool.submit(run,'mutation_r5/run_extra.py',['F_MATERIALIZER'],'mutation_r5/run_extra.log'))
    for future in futures:future.result()
