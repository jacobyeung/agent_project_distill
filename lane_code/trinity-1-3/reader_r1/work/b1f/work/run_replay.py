from pathlib import Path
import os,subprocess,time,json,sys
W=Path(__file__).resolve().parents[1];start=time.time();env=dict(os.environ,NP='6',OUT=str(W/'out/replay_patched.jsonl'),PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',TMPDIR=str(W/'work/tmp'))
cmd=[sys.executable,'-B',str(W/'work/replay_patched.py')]
with (W/'out/replay.log').open('w') as f:p=subprocess.run(cmd,cwd=W.parent/'b1/in/replay',env=env,stdout=f,stderr=subprocess.STDOUT)
with (W/'out/TESTS.txt').open('a') as f:f.write(json.dumps(dict(command=cmd,cwd=str(W.parent/'b1/in/replay'),exit=p.returncode,seconds=time.time()-start,log='replay.log'))+'\n')
raise SystemExit(p.returncode)
