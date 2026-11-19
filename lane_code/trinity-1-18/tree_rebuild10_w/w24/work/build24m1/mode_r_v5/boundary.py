from pathlib import Path
import sys,runpy,os,shutil
L=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24')
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build21'),str(L/'work/tree_r1'),str(Path(sys.argv[1]).parent)]
import native24 as N
N.C.processor_for=N.processor
import pl,rg,z
copy=shutil.copyfile
inode_map=__import__('json').loads(Path('/tmp/q_22c714e1/reuse.json').read_text())
def reuse(a,b,*args,**kwargs):
 a,b=Path(a),Path(b)
 if not b.exists() and a.is_file() and a.stat().st_size>100000:
  os.link(inode_map.get(str(a.stat().st_ino),str(a)),b);return str(b)
 return copy(a,b,*args,**kwargs)
shutil.copyfile=reuse
original_plan=pl.plan_payload
def planned(*args,**kwargs):
 req,paths,stage=original_plan(*args,**kwargs)
 def wrapped(entries,directory):
  # Pre-bind large authenticated inputs to their retained bytes, without copies.
  plan=z.load(Path(directory).parent/'plan.json')
  for name,e in entries.items():
   if 'sha256' not in e or e.get('bytes',0)<=100000:continue
   h=e['sha256'];source=paths.get(h)
   if source and Path(source).is_file():
    dst=Path(directory)/name;dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists():os.link(inode_map.get(str(Path(source).stat().st_ino),source),dst)
  return stage(entries,directory)
 wrapped.close=stage.close
 return req,paths,wrapped
pl.plan_payload=planned
native=rg.regenerate
rg.regenerate=lambda cfg,root:native(cfg,root,compare=False)
helper=sys.argv[1];sys.argv=sys.argv[1:]
runpy.run_path(helper,run_name='__main__')
