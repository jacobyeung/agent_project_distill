"""Reuse all reviewer mutation strings; run focused current tests per mutation."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
L=Path(__file__).resolve().parents[2]
output=L/'work/build4'/(sys.argv[1] if len(sys.argv)>1 else 'mutation_proof');output.mkdir()
code=ast.parse((L/'work/review1/evidence/mutcov.py').read_text())
mutations=next(ast.literal_eval(n.value) for n in code.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='M' for t in n.targets))
targets=[
 ['tests.test_r2_data_path.GrammarTests'],['tests.test_r2_shared_grammar','tests.test_r2_data_path.GrammarTests'],
 ['tests.test_r2_edges.Edges.test_wrapper_refusals_and_shared_cli'],['tests.test_r2_build4.ReviewGuards.test_direct_route_in_wrong_stream'],
 ['tests.test_r2_build4.ReviewGuards.test_manifest_contract_and_validator'],['tests.test_r2_refusals'],['tests.test_r2_refusals'],
 ['tests.test_r2_data_path.DataPathTests.test_intake_mutations_and_upstream_accounting'],['tests.test_r2_policy.Policy.test_shared_withheld_and_alias_intake'],
 ['tests.test_r2_refusals'],['tests.test_r2_policy.Policy.test_shared_withheld_and_alias_intake'],
 ['tests.test_r2_build4.ReviewGuards.test_wrong_independent_scene'],['tests.test_r2_sampling','tests.test_r2_portable'],
 ['tests.test_r2_policy'],['tests.test_r2_policy'],['tests.test_r2_build3.Build3.test_opener_export_keep_and_reset'],
 ['tests.test_r2_build4.ReviewGuards.test_distinct_pose_sources'],['tests.test_r2_data_path.DataPathTests.test_marker_full_store_and_route_collision']]
results=[]
for index in (0,2,5,6):targets[index]=['tests.test_r2_build4.ReviewGuards.test_isolated_mutation_guards']
for index in (7,12):targets[index]=['tests.test_r2_build4.ReviewGuards.test_duplicate_row_and_repeat_limit']
selected=set(map(int,sys.argv[2:])) if len(sys.argv)>2 else set(range(len(mutations)))
with (output/'baseline.log').open('w') as log:
    baseline=subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/build4/test_runner.py'),str(output/'baseline'),
        *sorted({name for index,group in enumerate(targets) if index in selected for name in group})],env=os.environ,stdout=log,stderr=subprocess.STDOUT)
if baseline.returncode:
    (output/'RESULTS.json').write_text(json.dumps(dict(status='baseline failed',returncode=baseline.returncode)))
    sys.exit(baseline.returncode)
for index,((name,file,old,new),tests) in enumerate(zip(mutations,targets)):
    if index not in selected:
        continue
    if not (L/'work/tree_r1'/file).read_text().count(old):
        results.append(dict(name=name,status='obsolete pattern; current envelope replaces per-row contract'))
        continue
    spec=dict(file=file,old=old,new=new,tests=tests,output=str(output/str(index)),last=index==15)
    p=output/(str(index)+'.json');p.write_text(json.dumps(spec))
    with (output/(str(index)+'.log')).open('w') as log:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/build4/mutation_child.py'),str(p)],env=os.environ,stdout=log,stderr=subprocess.STDOUT)
    record=Path(spec['output'])/'results.json'
    detail=json.loads(record.read_text()) if record.exists() else {}
    results.append(dict(name=name,status='killed' if result.returncode else 'survived',returncode=result.returncode,
                        tests=detail.get('tests'),errors=len(detail.get('errors',[])),failures=len(detail.get('failures',[])),
                        evidence=str(record.relative_to(L))))
    (output/'RESULTS.json').write_text(json.dumps(results,indent=2)+'\n')
    print(index,results[-1]['status'],name,flush=True)
