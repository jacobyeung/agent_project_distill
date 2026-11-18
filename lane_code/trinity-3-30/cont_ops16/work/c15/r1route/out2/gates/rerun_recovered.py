from pathlib import Path
import os,subprocess,json
G=Path(__file__).resolve().parent;R=G.parent;env=dict(os.environ,PATH='/usr/bin:/bin',OMP_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',MKL_NUM_THREADS='8',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(G/'tmp'),XDG_CACHE_HOME=str(G/'cache'),HF_HOME=str(G/'cache/hf'),CUDA_VISIBLE_DEVICES='')
(G/'tmp').mkdir(exist_ok=True);(G/'results').mkdir(exist_ok=True)
py='/scratch/jjyeung/envs/p1cpu/bin/python'
for mode in ('base','release'):
 for k in ('b1','b2'):
  o=G/mode/k
  suites=[('package',o/'tests/test_package.py',[]),('constraints',o/'tests/test_constraints.py',[])] if mode=='base' else [('package',G/'test_release_package.py',[str(o)])]
  suites += [('sequence',o/'work/test_sequence.py',[]),('memory',o/'work/test_operator_memory.py',[]),('guard',G/('bundle_regression.py' if mode=='base' else 'release_bundle.py'),[str(o)])]
  if k=='b2':suites += [(n,o/'work'/('test_'+n+'.py'),[]) for n in ('cpu_helper','room_pair','room_pair_labels')]
  if k=='b1' and mode=='base':suites += [('tower_pair',o/'test_tower_pair.py',[]),('return_stop',o/'test_b1_report.py',[])]
  if mode=='release':suites += [('return_stop',o/'work/test_fixes.py',[])]
  for name,path,args in suites:
   stem=mode+'_'+k+'_'+name
   if stem not in {'base_b1_package','base_b1_constraints','base_b1_guard','base_b1_return_stop','base_b2_constraints','base_b2_guard','base_b2_cpu_helper','release_b1_guard','release_b2_package','release_b2_guard','release_b2_cpu_helper','release_b2_return_stop'}:continue
   result=G/'results'/(stem+'.json')
   with (G/'results'/(stem+'.log')).open('w') as log:
    p=subprocess.run([py,'-B',str(G/'run_one.py'),str(path),str(result)]+args,env=env,cwd=R,stdout=log,stderr=subprocess.STDOUT)
   print(stem,p.returncode,json.loads(result.read_text())['counts'] if result.exists() else 'NO RESULT',flush=True)
