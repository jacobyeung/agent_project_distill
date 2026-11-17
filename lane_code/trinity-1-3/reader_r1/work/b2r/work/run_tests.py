import os,subprocess,sys,time,json
from pathlib import Path
W=Path(__file__).resolve().parents[1];O=W/'out';env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','XDG_CACHE_HOME':str(W/'work/cache'),'HF_HOME':str(W/'work/hf'),'TMPDIR':str(W/'work/tmp')}
files=sys.argv[1:] or ['out/tests/test_package.py','work/test_sequence.py','work/test_memo.py','work/test_memo_binding.py','work/test_module_selection.py','work/test_operator_memory.py','work/test_fixes.py','work/test_return_cli.py']
for f in files:
 start=time.time();cmd=[sys.executable,'-B',f];r=subprocess.run(cmd,cwd=W,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 log=O/(Path(f).stem+'_'+str(time.time_ns())+'.log');log.write_text(r.stdout)
 with (O/'TESTS.txt').open('a') as out:out.write(f'{"PASS" if r.returncode==0 else "FAIL"} {f} exit={r.returncode} seconds={time.time()-start:.2f} log={log.name}\n')
 print(f,r.returncode,flush=True)
 if r.returncode:print(r.stdout[-5500:],flush=True)
