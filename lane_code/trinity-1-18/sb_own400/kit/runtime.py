"""Authenticate local archives and reuse the sealed restoration and native own method."""
import ast,io,os,sys,tarfile,types
from core import *
class Joined(io.RawIOBase):
 def __init__(self,paths):self.paths=iter(paths);self.f=None
 def readable(self):return True
 def readinto(self,b):
  while True:
   if self.f is None:
    try:self.f=open(next(self.paths),'rb')
    except StopIteration:return 0
   n=self.f.readinto(b)
   if n:return n
   self.f.close();self.f=None
 def close(self):
  if self.f:self.f.close()
  super().close()
def extract(paths,dest):
 dest=contained(dest);dest.mkdir(parents=True,exist_ok=True)
 with io.BufferedReader(Joined(paths)) as stream,tarfile.open(fileobj=stream,mode='r|*') as archive:
  for m in archive:
   p=dest/m.name
   if pathlib.Path(m.name).is_absolute() or '..' in pathlib.Path(m.name).parts or not p.resolve().is_relative_to(dest):raise Refusal('Unsafe archive member: '+m.name)
   if m.isdir():p.mkdir(parents=True,exist_ok=True);continue
   if not m.isfile():raise Refusal('Nonregular archive member: '+m.name)
   p.parent.mkdir(parents=True,exist_ok=True)
   with archive.extractfile(m) as src,p.open('xb') as dst:
    while True:
     b=src.read(1048576)
     if not b:break
     dst.write(b)
   p.chmod(m.mode & 0o777)
def code(out):
 src=out/'source';receipt=out/'SOURCE_READY.json';pin={str(KIT/'inputs/A10b_code.tgz'):sha(KIT/'inputs/A10b_code.tgz')}
 if receipt.exists():
  rec=read(receipt)
  if rec['input_sha256']!=pin:raise Refusal('Source archive changed')
  for p,h in rec['files'].items():checked(p,h)
 else:
  if src.exists():raise Refusal('Incomplete source extraction; preserve it and use a fresh output')
  extract([KIT/'inputs/A10b_code.tgz'],src)
  atomic(receipt,{'input_sha256':pin,'files':{str(p):sha(p) for p in src.rglob('*') if p.is_file()}})
 os.environ['LEGS1_TREE']=str(src/'tree')
 sys.path[:0]=[str(KIT/'vendor/native'),str(src/'b'),str(src/'tree')]
 return src
def boundary_method():
 # Compile the exact GPU.own AST. Its original GPU constructor hardcodes step 544.
 import numpy as np,common
 p=KIT/'vendor/native_kit/boundaries.py';tree=ast.parse(p.read_text());cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='GPU');fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='own')
 B=types.SimpleNamespace(load=read,checked=lambda pin:checked(pin['path'],pin['sha256']),common=common)
 ns={'B':B,'np':np};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),'exec'),ns)
 return ns['own']
def authenticate_frames(captures):
 pins={}
 for c in captures:
  assert c['k1_split']=='train' and len(c['anchor_indices'])==32
  for f in c['model_row']['student_input']['frames']:
   if f['path'] not in pins:checked(f['path'],f['sha256']);pins[f['path']]=f['sha256']
 return pins
def stage(out):
 src=code(out);data=out/'assets';archives=read(KIT/'inputs/ARCHIVES.json');pins={str(KIT/'inputs/ARCHIVES.json'):sha(KIT/'inputs/ARCHIVES.json')}
 # Verify every archive part before any extraction or model allocation.
 for arc in archives['archives']:
  concat=__import__('hashlib').sha256()
  for part in arc['parts']:
   p=checked(part['path'],part['sha256'],part['bytes']);pins[str(p)]=part['sha256']
   with p.open('rb') as f:
    for b in iter(lambda:f.read(1048576),b''):concat.update(b)
  if concat.hexdigest()!=arc['sha256']:raise Refusal('Concatenated archive hash differs')
 ready=out/'ASSETS_READY.json'
 if ready.exists():
  rec=read(ready)
  if rec['input_sha256']!=pins:raise Refusal('Asset inputs changed')
  for p,h in rec['files'].items():checked(p,h)
 else:
  if data.exists():raise Refusal('Incomplete asset extraction; preserve it and use a fresh output')
  import shutil
  if shutil.disk_usage(out).free<100*1024**3+sum(a['expanded_bytes'] for a in archives['archives']):raise Refusal('Scratch free reserve would be below 100 GiB')
  for arc in archives['archives']:extract([p['path'] for p in arc['parts']],data)
  atomic(ready,{'input_sha256':pins,'files':{str(p):sha(p) for p in data.rglob('*') if p.is_file()}})
 export=read(KIT/'inputs/EXPORT_PINS.json')
 for name,rel in [('artifact','m400/artifact.json'),('heads','m400/heads.pt'),('full_weights','m400/full_weights/full_weights.json')]:checked(data/rel,export[name]['sha256'],export[name]['bytes'])
 for name,p in export['preparation'].items():checked(data/p['path'],p['sha256'],p['bytes'])
 full=read(data/'m400/full_weights/full_weights.json')
 for item in full['files']+[full['index']]:checked(data/'m400/full_weights'/item['name'],item['sha256'],item.get('bytes'))
 from parity_kit.stage_restore import stage as restore
 import parity_kit.run_parity as parity_run
 def configure_output(dest):
  dest=contained(dest);dest.mkdir(parents=True,exist_ok=True)
  for var,name in [('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('HF_HOME','hf'),('TRITON_CACHE_DIR','triton'),('TORCH_HOME','torch')]:
   path=out/name;path.mkdir(exist_ok=True);os.environ[var]=str(path)
 parity_run.configure_output=configure_output
 restored=out/'restored'
 if not (restored/'RESTORE.json').exists():
  restore(data/'m400/full_weights',data/'m400',src/'b/work/meta/x',restored,request=src/'b/work/n13/ret/native/paired/request.json',tree=src/'tree',base_assets=data/'b',model_manifest_tar=data/'o/model_8005668fc14ce5ee.tar',export_pins=export,data_root=data)
 # The vendor helper sets TMPDIR to its historical lane; restore our output containment.
 os.environ['TMPDIR']=str(out/'tmp');(out/'tmp').mkdir(exist_ok=True)
 pins.update({str(p):sha(p) for p in data.rglob('*') if p.is_file()})
 pins[str(restored/'RESTORE.json')]=sha(restored/'RESTORE.json')
 return src,data,restored,pins
def real_boundary(out,device):
 import torch
 torch.set_num_threads(8)
 src,data,restored,pins=stage(out)
 from e2e_reader.parity import load_native
 model,processor,info=load_native(restored,device=device,settings={'tree':str(src/'tree'),'config':str(data/'p0/config.json')})
 class Boundary:own=boundary_method()
 b=Boundary();b.model=model;b.processor=processor;b.device=device;b.info=info
 b.settings={'config':{'path':str(data/'p0/config.json'),'sha256':sha(data/'p0/config.json')}}
 return b,pins
