"""Fresh-process import provenance and inherited package admission, CPU only."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
import build_depth as BD
import json
import subprocess
import tempfile
sys.path.insert(0,str(BD.GB/'gpkg'))
import import_smoke as S
root=Path(tempfile.mkdtemp(dir=HERE/'tests',prefix='import_'))
BD.B.extract((HERE/'out/delivery.tgz').read_bytes(),root/'package')
BD.B.extract((root/'package/0.tgz').read_bytes(),root/'p')
results=[]
for code,tail in [(S.CHILD,['fixed']),(S.OPERATOR,[])]:
    p=subprocess.run([sys.executable,'-I','-s','-B','-c',code,str(root/'p'),str(root/'package'),*tail],
        cwd=HERE,env=os.environ.copy(),text=True,capture_output=True,timeout=60)
    results.append(dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
(HERE/'out/IMPORT_CHECK.json').write_text(json.dumps(dict(passed=all(x['returncode']==0 for x in results),checks=results),indent=2)+'\n')
print(json.dumps(dict(passed=all(x['returncode']==0 for x in results),returncodes=[x['returncode'] for x in results])))
raise SystemExit(any(x['returncode'] for x in results))
