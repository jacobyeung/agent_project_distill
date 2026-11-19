#!/usr/bin/env -S nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B
"""Print the decoded/localised N input identity using the sealed tree in a hidden view.
The preparation producer can change identity-bearing fields; this is not a claim
that an unavailable production RESULT.json has this final training identity.
"""
from pathlib import Path
import base64,json,os,subprocess,sys


def read(path):
 v=json.loads(Path(path).read_text())
 if 'payload' in v:
  raw=base64.b64decode(v['payload'],validate=True)
  if __import__('hashlib').sha256(raw).hexdigest()!=v['sha256']:raise ValueError('R1_CAPSULE_CHANGED')
  return json.loads(raw)
 return v


def localized(value,namespace):
 if isinstance(value,dict):return {k:localized(v,namespace) for k,v in value.items()}
 if isinstance(value,list):return [localized(v,namespace) for v in value]
 if isinstance(value,str) and value.startswith('u/'):return namespace+'/'+value
 return value


def compute(base):
 base=Path(base);kit=base/'work/build24/kits/n';spec=read(kit/'k/p.json')
 cfg=localized(read(kit/'k/n.json'),spec['namespace'])
 dest=base/'out/N_PRODUCTION_CONFIG.json'
 dest.write_text(json.dumps(cfg,sort_keys=True,indent=2)+'\n')
 args=['/usr/bin/bwrap','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc','--proc','/proc','--dev','/dev','--tmpfs','/tmp',
 '--ro-bind','/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu','/opt/py',
 '--ro-bind','/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages','/opt/site',
 '--ro-bind',str(base/'work/tree_r1'),'/tmp/s','--ro-bind',str(dest),'/tmp/c.json','--chdir','/tmp']
 code="import sys,json;from pathlib import Path;sys.path[:0]=['/opt/site','/tmp/s'];assert all(not Path(p).exists() for p in ('/scratch/jjyeung','/home','/data','/data2','/data3'));from student_pilot.carrier_c1_run import identity;print(identity(json.loads(Path('/tmp/c.json').read_text())))"
 p=subprocess.run(args+['/opt/py/bin/python3.12','-I','-s','-B','-c',code],text=True,capture_output=True,check=True)
 value=p.stdout.strip()
 if len(value)!=64:raise ValueError('R1_CONFIG_IDENTITY_INVALID')
 (base/'out/N_IDENTITY.txt').write_text(value+'\n')
 return value


if __name__=='__main__':
 import resource
 resource.setrlimit(resource.RLIMIT_AS,(19_000_000_000,19_000_000_000))
 os.environ.update(OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='')
 print(compute(Path(__file__).resolve().parents[1]))
