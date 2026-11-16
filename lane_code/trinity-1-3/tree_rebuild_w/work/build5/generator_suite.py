"""Check generator modules and compare their failures on the untouched base copy."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
L=Path(__file__).resolve().parents[2]
tree=L/'work/tree_r1'
names=['.'.join(p.relative_to(tree).with_suffix('').parts) for p in sorted((tree/'generator').rglob('test_*.py'))]
env={**os.environ,'R2_LANE_ROOT':str(L),'R2_ALL_TESTS':'0'}
def run(kind,path,names):
    output=L/'work/build5/proofs'/('generator_'+kind);output.mkdir(parents=True,exist_ok=True)
    env['R2_TREE']=str(path)
    if names:
        with (output/'console.log').open('w') as log:
            result=subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/build5/test_runner.py'),str(output),*names],
                                  env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode<0:raise RuntimeError('Generator process was killed; stop without retry')
        value=json.loads((output/'results.json').read_text())
    else:
        value=dict(tests=0,passed=[],failures=[],errors=[],skips=[],fatal=None,complete=True)
        (output/'results.json').write_text(json.dumps(value)+'\n')
    print(json.dumps(dict(kind=kind,tests=value['tests'],passed=len(value['passed']),
                         failures=len(value['failures']),errors=len(value['errors']),fatal=value['fatal'])),flush=True)
    return value
current=run('tree',tree,names)
base=L/'work/tmp/package/work/base/tree_b01ce449'
selected=[]
for name,error in current['failures']+current['errors']:
    match=re.search(r'generator\.derivgen_v7\.test_[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*',name)
    if match:selected.append(match.group())
prior=run('base',base,sorted(set(selected)))
old={name:error for name,error in prior['failures']+prior['errors']}
regressions=[dict(test=name,error=error) for name,error in current['failures']+current['errors'] if name not in old]
record=dict(tree_source='work/build5/proofs/generator_tree/results.json',
            base_source='work/build5/proofs/generator_base/results.json',regressions=regressions,
            complete=current.get('complete') and prior.get('complete'))
(L/'work/build5/GENERATOR_COMPARISON.json').write_text(json.dumps(record,indent=2)+'\n')
for row in regressions:print(row['test'],row['error'][-2000:])
