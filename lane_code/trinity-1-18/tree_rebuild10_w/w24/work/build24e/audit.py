from pathlib import Path
import sys,json,collections
L=Path(__file__).resolve().parents[2];D=L/"work/build24e"
sys.path.insert(0,str(L/"work/build24"));import joblib as J
rows=[]
def walk(v,where):
 if isinstance(v,dict):
  if "path" in v and "sha256" in v:rows.append(dict(kind="pin",where=where,path=v["path"],sha256=v["sha256"]))
  for k,x in v.items():walk(x,where+"."+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):walk(x,where+"."+str(i))
 elif isinstance(v,str) and v.startswith("/"):rows.append(dict(kind="absolute",where=where,path=v))
for name in ("q","n","n_go"):
 k=L/"out/kit_n_go" if name=="n_go" else L/"work/build24/kits"/name
 for p in sorted((k/"k").glob("*.json")):
  try:walk(J.load(p),name+"/k/"+p.name)
  except (ValueError,UnicodeDecodeError):pass
J.write(D/"PATHS_BEFORE.json",rows)
unique={r["path"]:r for r in rows if r["kind"]=="pin"};print("pins",len(unique),"absolute",len({r["path"] for r in rows if r["kind"]=="absolute"}))
for p,r in unique.items():
 if p.startswith("/scratch/jjyeung") or p.startswith("/home") or p.startswith("/data"):print(r["where"],p,r["sha256"],Path(p).is_file())
print("OTHER ABSOLUTES")
for p in sorted({r["path"] for r in rows if r["kind"]=="absolute"} - set(unique)):print(p)
