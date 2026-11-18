from pathlib import Path
import os,subprocess,json
W=Path.cwd();env=dict(os.environ,PATH='/usr/bin:/bin',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(W/'tmp'))
for k in ('b1','b2'):
 cmds=[('package',['test_release_package.py','release/'+k]),('guard',['release_bundle.py','release/'+k])]
 for name,src in [('sequence','work/test_sequence.py'),('memory','work/test_operator_memory.py'),('return_stop','work/test_fixes.py')]+([('cpu_helper','work/test_cpu_helper.py'),('room_pair','work/test_room_pair.py'),('room_labels','work/test_room_pair_labels.py')] if k=='b2' else []):
  cmds.append((name,['run_suite.py','release/'+k+'/'+src,'release/'+k+'/tests_'+name+'_result.json']))
 for name,args in cmds:
  with (W/'out'/k/('release_'+name+'.log')).open('w') as f:r=subprocess.run(['/scratch/jjyeung/envs/p1cpu/bin/python','-B']+args,env=env,stdout=f,stderr=subprocess.STDOUT)
  p=W/'release'/k/('tests_'+name+'_result.json')
  if p.exists():(W/'out'/k/('release_'+name+'_result.json')).write_bytes(p.read_bytes())
  print(k,name,r.returncode,flush=True)
