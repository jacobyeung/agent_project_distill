from pathlib import Path
import ast,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23c';A=L/'attic/build23c';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
from launch_r2.build import capsule_json
guard='''import json,os,torch
a=False;c=0;n=None;m=None;x=False
try:
 a=torch.cuda.is_available()
 c=torch.cuda.device_count()
 if a and c:
  p=torch.cuda.get_device_properties(0)
  n=p.name;m=p.total_memory
except Exception:
 x=True
print(json.dumps(dict(v=torch.__version__,a=a,c=c,e=os.environ.get('CUDA_VISIBLE_DEVICES'),n=n,m=m,d0=os.path.exists('/dev/nvidia0'),dc=os.path.exists('/dev/nvidiactl'),x=x)),flush=True)
if x or not a or c<1 or m is None or m < 75*(1<<30):
 raise RuntimeError('E42')
'''
p=B/'kit.py';source=p.read_text()
old="""import torch
if not torch.cuda.is_available() or torch.cuda.get_device_properties(0).total_memory < 80*(1<<30):
 raise RuntimeError('E42')
"""
assert source.count(old)==1 and (K/'b/g.py').read_text()==old
p.rename(A/'kit.py');p.write_text(source.replace(old,guard).replace('minimum_gpu_gib=80','minimum_gpu_gib=75'))
# Regenerate only the guard literal: the full legacy builder would replace the
# authenticated build-23b config. No sealed-source or config generator is run.
nodes=[n for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='write_text' and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value==guard]
assert len(nodes)==1
(K/'b/g.py').rename(A/'g.py');(K/'b/g.py').write_text(ast.literal_eval(nodes[0].args[0]))
(K/'SHA256SUMS.txt').rename(A/'SHA256SUMS.txt')
manifest={str(p.relative_to(K)):J.sha(p) for p in K.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
(K/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(manifest.items())))
record=J.load(K/'BUILD.json');(K/'BUILD.json').rename(A/'BUILD.json')
record.update(GO=False,kit_sha256=J.seal(K));record['resource_request']['minimum_gpu_gib']=75
(K/'BUILD.json').write_bytes(capsule_json(record))
old_uploads=J.load(A/'UPLOADS.json')
all_uploads=[x for x in old_uploads['files'] if x['opaque_name'].startswith('u/')]+[
 dict(local_path=str(p),opaque_name='q/'+str(p.relative_to(K)),bytes=p.stat().st_size,sha256=J.sha(p)) for p in sorted(K.rglob('*')) if p.is_file()]
J.write(B/'UPLOADS.json',dict(files=all_uploads,total_bytes=sum(x['bytes'] for x in all_uploads)))
before={v['opaque_name']:v for v in old_uploads['files']};after={v['opaque_name']:v for v in all_uploads}
changed=[v for n,v in after.items() if n not in before or before[n]['sha256']!=v['sha256']]
assert {v['opaque_name'] for v in changed}=={'q/b/g.py','q/SHA256SUMS.txt','q/BUILD.json'}
assert set(before)==set(after)
J.write(L/'out/UPLOADS_NEW_23C.json',changed)
J.write(D/'KIT.json',dict(GO=False,tree_seal=record['source_seal'],kit_seal=J.seal(K),changed=[x['opaque_name'] for x in changed],upload_bytes=sum(x['bytes'] for x in changed)))
print(json.dumps(J.load(D/'KIT.json'),indent=2))
