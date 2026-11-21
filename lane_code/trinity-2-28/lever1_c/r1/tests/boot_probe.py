"""Run the delivered numeric worker with a local interpreter binding."""
import json,os,sys,tarfile,tempfile,time,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
root=Path(tempfile.mkdtemp(dir=HERE/'tests',prefix='pre_'));package=root/'package';package.mkdir();p=root/'p';p.mkdir()
with tarfile.open(HERE/'out/delivery.tgz') as t:t.extractall(package,filter='data')
with tarfile.open(package/'0.tgz') as t:t.extractall(p,filter='data')
sys.path.insert(0,str(p));import l;l.install(p)
from orchard_h10.runner import control
from orchard_h10.common import write
config=dict(package=str(p),output=str(root/'r'),python=sys.executable,device='cpu',cache_root=str(root/'r/cache/0'),prefix=[])
c=control(config);write(c/'30.json',dict(action=3,boot=True,config=config,package=str(p),plan='local',job='173925'))
env=dict(PATH='/usr/bin:/bin',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
start=time.monotonic();r=subprocess.run([sys.executable,'-B','-I','5.py','30.json'],cwd=c,env=env,capture_output=True,text=True)
print(root, r.returncode,time.monotonic()-start);print(r.stderr[-5000:])
print((root/'r/metadata/25.json').read_text())
