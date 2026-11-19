from pathlib import Path
import sys,platform,json,hashlib
import torch,transformers,numpy,PIL
W=Path(__file__).resolve().parents[1]
paths=[Path(sys.executable).resolve(),Path(__file__).resolve(),Path(torch.__file__),Path(transformers.__file__),Path(numpy.__file__),Path(PIL.__file__)]
result=dict(input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},python=sys.version,executable=sys.executable,torch=torch.__version__,transformers=transformers.__version__,numpy=numpy.__version__,pillow=PIL.__version__,host=platform.node(),device='cpu',thread_limit=16,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/environment.py')
(W/'out/ENVIRONMENT.json').write_text(json.dumps(result,indent=2)+'\n')
print(result['host'],result['torch'])
