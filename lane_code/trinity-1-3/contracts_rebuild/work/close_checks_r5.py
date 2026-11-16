from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,shutil,subprocess,sys
L=Path(__file__).resolve().parents[1];P=sys.executable
def run(script,args=(),log=None):
    path=L/'work'/script
    with (L/'work'/(log or (Path(script).stem+'_close.log'))).open('w') as stream:
        result=subprocess.run([P,'-I','-s','-B',str(path),*map(str,args)],stdout=stream,stderr=subprocess.STDOUT)
    assert result.returncode==0,(script,result.returncode,log)
    print(script,'PASS',flush=True)
proof=(L/'work/apply_proof_r5.py').read_text().replace('r5_proof','r5_close_proof').replace('r5_snapshot','r5_close_snapshot')
(L/'work/apply_close_r5.py').write_text(proof)
p=L/'work/trees/r5_close_proof/base';p.parent.mkdir(exist_ok=True);shutil.copytree(L/'work/base/work/base/tree_b01ce449',p)
for f in [p,*p.rglob('*')]:f.chmod(f.stat().st_mode & ~0o222)
run('build_packet_r5.py');run('apply_close_r5.py')
with ThreadPoolExecutor(max_workers=3) as pool:
    futures=[pool.submit(run,'run_tests_r5.py',[tree,tag,'contract'],log) for tree,tag,log in (
        ('r5_close_proof/base','B8_CLOSE_R5','tests_close_r5.log'),
        ('r5_close_snapshot','B8_CLOSE_SNAPSHOT_R5','tests_close_snapshot_r5.log'))]
    futures.append(pool.submit(run,'run_tests_r5.py',['r5_close_proof/base','B8_CLOSE_COVERAGE_R5','tree',L/'work/coverage_probes_r5.py'],'coverage_close_r5.log'))
    for future in futures:future.result()
s=(L/'work/mutation_r5/run_verified.py').read_text().replace('round_verified','round_close').replace('MUTATION_VERIFIED_','MUTATION_CLOSE_')
s=s.replace("mutants += [\n ('F_METRIC", "mutants += [\n ('F_GROUND_METRIC','student_pilot/ground_lifting.py','if metric_only and new_contracts() and not heading_available(geometry):','if False:'),\n ('F_METRIC")
s=s.replace("selectors.update({", "selectors.update({\n 'F_GROUND_METRIC':'grounded_calculator_metric_basis',")
(L/'work/mutation_r5/run_close.py').write_text(s)
s=(L/'work/replay_run_r5.py').read_text().replace('completed_r5','closed_r5')
(L/'work/replay_close_r5.py').write_text(s)
p=L/'work/real_replay_r5/summarize.py';p.write_text(p.read_text().replace('completed_r5','closed_r5'))
def attacks():
    tree=L/'work/trees/r5_applied';A=L/'work/test_artifacts_r5'
    run('review2_inputs/attack_r4_angle.py',[tree,A/'ROTATED_ANGLE_R5.json'],'angle_close_r5.log')
    run('review2_inputs/attack_r4_heading.py',[tree,A/'HEADING_ATTACK_R5.json'],'heading_close_r5.log')
    run('review2_inputs/attack_m4.py',[tree],'binding_close_r5.log')
    run('review2_inputs/rerender_depth.py',[tree],'depth_close_r5.log')
    run('review2_inputs/prov313.py',[tree,'off'],'provider_close_r5.log')
    run('replay_sensor313_r5.py',['off'],'sensor_replay_close_r5.log')
with ThreadPoolExecutor(max_workers=4) as pool:
    futures=[pool.submit(run,'mutation_r5/run_close.py',(), 'mutation_r5/run_close.log'),
             pool.submit(run,'regenerate_r5.py',(),'regenerate_close_r5.log'),
             pool.submit(run,'replay_close_r5.py',(),'replay_close_r5.log'),pool.submit(attacks)]
    for future in futures:future.result()
print('ALL CLOSING EXECUTIONS PASSED',flush=True)
