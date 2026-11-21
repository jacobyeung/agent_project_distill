"""Local path binding, bounded publication, and a CPU planning probe."""
import base64,gzip,hashlib,json,os,sys,tarfile
from pathlib import Path

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def load(p):
 v=json.loads(Path(p).read_bytes())
 if isinstance(v,dict) and v.get('encoding') in ('base64','base64-json'):
  raw=base64.b64decode(v['payload'],validate=True)
  if hashlib.sha256(raw).hexdigest()!=v['sha256']:raise ValueError('E01')
  return json.loads(raw)
 return v

def write(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')

def remap(source,physical,output):
 physical=Path(physical).resolve();value=load(source);rules=[];logical=Path('/tmp/q_22c714e1')
 for old in value['remove_files']:
  row=dict(old);p=Path(row['path'])
  if p.is_absolute():
   if not p.is_relative_to(logical):raise ValueError('E91')
   p=physical/p.relative_to(logical)
  else:p=physical/'p/q'/p
  if p.is_symlink() or not p.resolve().is_relative_to(physical) or sha(p)!=row['sha256']:raise ValueError('E92')
  row['path']=str(p.resolve());rules.append(row)
 write(output,dict(remove_files=rules))

def binary(kit):
 pin=load(Path(kit)/'k/l.json')['bwrap']
 if sha(pin['file'])!=pin['sha256']:raise ValueError('E93')
 print(pin['file'])

def publish(node,target,kit,code,slurm_log=None,slurm_err=None):
 node,target,kit=map(Path,(node,target,kit));target.mkdir(parents=True,exist_ok=True)
 # Reserve 1.2 MB for j2 and its in-progress replacements.
 budget=3_500_000;payload={};rows=[];missing=[];skipped=[]
 existing=[p for p in target.rglob("*") if p.is_file()]
 if any(p.name not in ("j2.log","j2.err","j2.log.part","j2.err.part") for p in existing):raise ValueError("E96")
 reserve=max(1_200_000,sum(p.stat().st_size for p in existing))
 source_names=["p/q/b/population.json","p/q/b/indices.json","p/q/b/reader_filters.json",
  "p/q/b/binding.json","p/q/b/receipt.json","p/q/h/receipt.json","p/q/h/config.json",
  "p/q/f.json","p/q/host.json","p/q/RESULT.json","p/q/selection/receipt.json"]
 fixed=[("j7/e"+str(i)+".json",node/p,None) for i,p in enumerate(source_names)]
 tails=[(name,node/"ev"/name,256*1024) for name in ("q.log","r.log","dbb.log","q.steps")]
 for name,path in (("j7/s.log",slurm_log),("j7/s.err",slurm_err)):
  if path is not None:tails.append((name,Path(path),256*1024))
 candidates=list(fixed)+tails;seen={p for _,p,_ in candidates}
 for p in sorted((node/"p/q/b").glob("*.json")):
  if p not in seen:candidates.append(("j7/b"+str(len(candidates))+".json",p,None));seen.add(p)
 for p in sorted((node/"p/q/a").rglob("*.json")):
  if p not in seen:candidates.append(("j7/a"+str(len(candidates))+".json",p,None));seen.add(p)
 for p in sorted((node/"ev").rglob("*")):
  if p.is_file() and p not in seen and p.name not in ("j2.log","j2.err",".l") and not p.name.endswith(".part"):
   candidates.append((str(p.relative_to(node/"ev")),p,None));seen.add(p)
 record=dict(returncode=int(code),kit_sha256=load(kit/"BUILD.json")["kit_sha256"],GO=False,
  files=rows,missing=missing,skipped=skipped,bytes=0,limit=5_000_000,j2_reserved_bytes=1_200_000)
 def encoded():return (json.dumps(record,sort_keys=True,separators=(",",":"))+"\n").encode()
 # Account for the complete skip inventory before admitting any payload.
 for name,p,tail in candidates:
  if not p.is_file():
   if (name,p,tail) in fixed:missing.append(name)
   continue
  if p.is_symlink() or (tail is None and p.stat().st_size>50_000_000):raise ValueError("E94")
  skipped.append(dict(name=name,bytes=min(p.stat().st_size,tail) if tail else p.stat().st_size))
 if reserve+len(encoded())>=5_000_000:raise ValueError("E95")
 pending=iter(list(skipped))
 for name,p,tail in candidates:
  if not p.is_file():continue
  item=next(pending)
  with p.open("rb") as f:
   if tail:f.seek(max(0,os.fstat(f.fileno()).st_size-tail))
   raw=f.read(tail if tail else 50_000_001)
  if tail is None and len(raw)>50_000_000:raise ValueError("E94")
  packed=gzip.compress(raw,mtime=0)
  if len(packed)<len(raw) or bytes([80,65,83,83]) in raw:name+=".gz";stored=packed
  else:stored=raw
  if name in payload or name=="j7.json":raise ValueError("E96")
  source=str(p.relative_to(node)) if p.is_relative_to(node) else str(p)
  row=dict(name=name,source=source,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),stored_bytes=len(stored),stored_sha256=hashlib.sha256(stored).hexdigest())
  if tail:row.update(tail_bytes=tail,source_bytes=p.stat().st_size)
  skipped.remove(item);rows.append(row);record["bytes"]+=len(stored)
  if record["bytes"]>budget or reserve+record["bytes"]+len(encoded())>=5_000_000:
   rows.pop();record["bytes"]-=len(stored);skipped.append(item)
  else:payload[name]=stored
 payload["j7.json"]=encoded()
 for name,raw in payload.items():
  p=target/name;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open("xb") as f:f.write(raw)
 if sum(p.stat().st_size for p in target.rglob("*") if p.is_file())>=5_000_000:raise ValueError("E95")
 return record

def probe(kit,node,pool):
 kit,node=Path(kit).resolve(),Path(node).resolve();node.mkdir(parents=True,exist_ok=True)
 os.environ['CUDA_VISIBLE_DEVICES']='';sys.path[:0]=[str(kit/'b')]
 import z
 seal=z.seal(kit);control=z.load(kit/'k/a.json')
 if control.get('GO') is not False or not control.get('discovery'):raise ValueError('E97')
 source=control['source'];archive=z.checked(kit/source['path'],source['sha256'])
 with tarfile.open(archive) as t:t.extractall(node/'s',filter='data')
 sys.path.insert(0,str(node/'s'));import pl
 result=dict(kit_sha256=seal,GO=False,mode='q',completed=False,selection_authenticated=False)
 try:
  pin,selected=pl.selection_pin(kit);result.update(selection_authenticated=True,selection_sha256=z.sha(selected),regenerated_sha256=z.load(selected)['regenerated_sha256'])
  z.resolve(kit,pool,None,node/'r.json')
  resolved=z.load(node/'r.json');root=node/'p';root.mkdir()
  request,paths,stage=pl.plan_payload(kit,resolved,root,regeneration=False)
  stage.close();result.update(completed=True,entries=len(paths))
 except Exception as e:
  result['error']=z.screen(type(e).__name__+':'+str(e),z.load(kit/'k/g.json'),z.load(kit/'b/wh.json'))
 write(node/'p0.json',result)
 return 0 if result['completed'] else 1

if __name__=='__main__':
 mode,*a=sys.argv[1:]
 if mode=='m':remap(*a)
 elif mode=='b':binary(*a)
 elif mode=='p':publish(*a)
 elif mode=='q':raise SystemExit(probe(*a))
 else:raise ValueError('E98')
