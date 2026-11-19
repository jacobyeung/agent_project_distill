from common import *
sys.path.insert(0,str(kit("q")/"b"))
from px import inventory
from z import selected400
records={};available={};originals={};sizes={}
def collect(v):
 if isinstance(v,dict):
  if isinstance(v.get("sha256"),str) and v.get("local_path"):
   h=v["sha256"];p=Path(v["local_path"])
   if p.is_file():available.setdefault(h,str(p));sizes[h]=v.get("bytes",p.stat().st_size)
  for x in v.values():collect(x)
 elif isinstance(v,list):
  for x in v:collect(x)
for p in sorted((L/"out").glob("UPLOADS*.json"))+[L/"work/build24m1/UPLOADS_q.json",L/"work/build24m1/UPLOADS_n.json"]:collect(J.load(p))
mroot=L.parent/"ext/m400real"
for row in J.load(mroot/"MANIFEST.json")["files"]:
 h=row["sha256"];sizes[h]=row["bytes"]
 try:selected400(row["path"])
 except ValueError:continue
 p=mroot/"files"/row["path"].lstrip("/")
 if p.is_file():available.setdefault(h,str(p));originals[row["path"]]=h
staged=inventory(kit("q"));spec=J.load(kit("q")/"k/p.json");uploads={x["sha256"] for x in spec["uploads"]}
small={}
for row in J.load(mroot/"MANIFEST.json")["files"]:
 try:selected400(row["path"])
 except ValueError:continue
 if row["bytes"]<5_000_000:small[row["sha256"]]=row
seen=set();needs={}
def closure(v,field):
 if isinstance(v,dict):
  if set(v)=={"path","sha256"}:
   h=v["sha256"];n=needs.setdefault(h,dict(sha256=h,bytes=sizes.get(h),fields=[],literal_path=v["path"],source=("upload" if h in uploads else "m400_metadata" if h in small else "staged_inventory" if h in staged else "MISSING"),staged=staged.get(h,[])))
   if field not in n["fields"]:n["fields"].append(field)
   if h in seen:return
   seen.add(h)
   p=available.get(h)
   if p and Path(p).stat().st_size<5_000_000:
    if J.sha(p)!=h:raise ValueError("LOCAL_RECEIPT_CHANGED:"+p)
    try:child=J.load(p)
    except (ValueError,UnicodeError):return
    if isinstance(child,dict):
     for key in ("database","model","division","dense_indices"):
      if key in child:closure(child[key],field+"."+key)
     for i,x in enumerate(child.get("sources",[])):
      if not isinstance(x,dict):continue
      for key in ("receipt","model","dense_plan","teacher","clips_plan"):
       if key in x:closure(x[key],field+".sources."+str(i)+"."+key)
   return
  for key,x in v.items():closure(x,field+"."+key)
 elif isinstance(v,list):
  for i,x in enumerate(v):closure(x,field+"."+str(i))
cfg=J.load(kit("q")/"k/n.json")
# Resolver replaces the pool recipe with the authenticated P runtime recipe.
pin=spec["p_run"]["config"];pconfig=J.load(available[pin["sha256"]]);cfg["s1_routing"]=pconfig["s1_routing"]
closure(cfg["streams"],"config.streams")
closure(pin,"config.r1_training.p_run.config")
pr=J.load(available[pconfig["streams"]["routing"]["sha256"]]);closure(pr["materialization"],"P.routing.materialization")
recipe=J.load(available[pr["materialization"]["sha256"]])
for key in ("remove_files","dev_scene_exclusions","benchmark_scene_exclusions"):closure(pconfig[key],"P.config."+key)
for key in ("inputs","legacy","division","base_model"):closure(recipe[key],"P.materialization."+key)
for field,catalog in (("config.s1_routing.catalog",cfg["s1_routing"].get("catalog",{})),("P.materialization.inputs.catalog",recipe["inputs"].get("catalog",{}))):
 for h,p in catalog.items():closure(dict(path=p,sha256=h),field+"."+h)
# Every other live config/request pin must also have a planned source.
closure(cfg,"config")
missing=[v for v in needs.values() if v["source"]=="MISSING"]
J.write(D/"PIN_AUDIT.json",dict(inputs=list(needs.values()),missing=missing,available=available,small=small))
print("pins",len(needs),"missing",len(missing))
for v in missing:print(v["sha256"],v["bytes"],v["fields"][:3])
