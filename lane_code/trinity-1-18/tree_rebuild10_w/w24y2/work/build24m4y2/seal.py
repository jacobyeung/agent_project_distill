from pathlib import Path
import sys,json,base64,hashlib,time
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4y2';T=L/'work/tree_r1c'
sys.path[:0]=[str(D),str(T),str(L/'out/kit_qd/b')]
import z
from student_pilot.source_seal import inventory,archive,check_archive
from student_pilot.p3_provenance import digest,file_pin
from launch_r1.build import verify
NAMES=('q','n','n_go','qd')
def kit(n):return L/('out/kit_'+n if n in ('n_go','qd') else 'work/build24/kits/'+n)
def write(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def replace(p,raw):
 p=Path(p);mode=p.stat().st_mode&511 if p.exists() else 0o644
 if p.exists():
  a=L/'attic/build24m4x2'/p.relative_to(L);a.parent.mkdir(parents=True,exist_ok=True)
  if a.exists():a=a.with_name(a.name+'.'+str(time.time_ns()))
  p.rename(a)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw.encode() if isinstance(raw,str) else raw);p.chmod(mode)
def cap(p,v):
 raw=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
 replace(p,json.dumps(dict(encoding='base64-json',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()))+'\n')
def reseal(k):
 files={str(p.relative_to(k)):z.sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('BUILD.json','SHA256SUMS.txt')}
 replace(k/'SHA256SUMS.txt',''.join(h+'  '+n+'\n' for n,h in sorted(files.items())))
 v=z.load(k/'BUILD.json');v['kit_sha256']=z.sha(k/'SHA256SUMS.txt');v['config_sha256']=z.sha(k/'k/c.json');cap(k/'BUILD.json',v)
 return verify(k)
def main():
 files=inventory(T);tree=digest(files);p=D/('t_'+tree[:16]+'.tar');archive(T,p,files,compress=True);check_archive(file_pin(p),files)
 sources=z.load(D/'SOURCES.json')['names'];seals={}
 for name in NAMES:
  k=kit(name)
  for rel in ('k/c.json','k/n.json'):
   v=z.load(k/rel);v.pop('extent_pool_sources',None);v['r1_training']['extent_pool_sources']=sources;cap(k/rel,v)
  for rel in ('k/7.json','k/c0.json'):
   v=z.load(k/rel);v.update(files=files,tree_sha256=tree,commit='sha256:'+tree)
   for key in ('sources','operation_sources'):v[key]={n:files[n] for n in v[key]}
   v['archive']['sha256']=z.sha(p);cap(k/rel,v)
  v=z.load(k/'k/a.json');replace(k/v['source']['path'],p.read_bytes());v['source'].update(sha256=z.sha(p),tree_sha256=tree);v['GO']=name=='n_go';cap(k/'k/a.json',v)
  spec=z.load(k/'k/p.json');old=spec['code_sha256'];raw=base64.b64decode(json.loads((k/'k/c0.json').read_text())['payload']);h=hashlib.sha256(raw).hexdigest();spec['code_sha256']=h
  for item in spec['uploads']:
   if item['sha256']==old:
    item.update(sha256=h,bytes=len(raw))
    for key in ('path','opaque_name','name'):
     if key in item:item[key]=item[key].replace(old,h)
  spec['pin_paths']={v['sha256']:spec['namespace']+'/u/'+v['sha256'] for v in spec['uploads']};cap(k/'k/p.json',spec)
  v=z.load(k/'k/c.json');v['code']=dict(path='k/7.json',sha256=z.sha(k/'k/7.json'));cap(k/'k/c.json',v)
  v=z.load(k/'k/n.json');v['code']=dict(path='u/'+h,sha256=h);cap(k/'k/n.json',v)
  dest=D/'u'/h;dest.parent.mkdir(exist_ok=True)
  if not dest.exists():dest.write_bytes(raw)
  v=z.load(k/'BUILD.json');v['source_seal']=tree;v['GO']=name=='n_go';cap(k/'BUILD.json',v)
  seals[name]=reseal(k)
 write(D/'SEALS.json',dict(tree=tree,kits=seals,archive=file_pin(p)))
 replace(L/'out/TREE_SEAL.json',json.dumps(dict(tree_sha256=tree,files=len(files)),indent=2)+'\n')
 replace(L/'out/TREE_FILES.sha256',''.join(h+'  '+n+'\n' for n,h in sorted(files.items())))
 print(json.dumps(dict(tree=tree,kits=seals),indent=2))
if __name__=='__main__':main()
