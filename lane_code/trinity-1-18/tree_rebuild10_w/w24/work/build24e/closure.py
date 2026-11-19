from pathlib import Path
import sys,json,base64,re,shutil
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";sys.path.insert(0,str(L/"work/build24"));import joblib as J
c=J.load(D/"CLOSURE.json");ups={v["sha256"]:v for v in J.load(L/"work/build24d/UPLOADS_q.json")["files"] if v["opaque_name"].startswith("u/")};ups.update(c["added"])
records=[];seen=set();pending=[];host={}
def scan(v,where):
 if isinstance(v,dict):
  if v.get("encoding") in ("base64-json","base64") and "payload" in v:
   raw=base64.b64decode(v["payload"]);assert __import__("hashlib").sha256(raw).hexdigest()==v["sha256"]
   try:scan(json.loads(raw),where+".$decoded")
   except (ValueError,UnicodeError):pass
  if isinstance(v.get("dest"),str) and "sha256" in v:host[v["sha256"]]=v["dest"]
  if isinstance(v.get("path"),str) and re.fullmatch("[a-f0-9]{64}",str(v.get("sha256",""))):
   r=dict(kind="pin",where=where,path=v["path"],sha256=v["sha256"]);records.append(r);pending.append(r)
  for key,x in v.items():
   if key!="payload":scan(x,where+"."+key)
 elif isinstance(v,list):
  for i,x in enumerate(v):scan(x,where+"."+str(i))
 elif isinstance(v,str) and v.startswith("/"):records.append(dict(kind="absolute",where=where,path=v))
for name in ("q","n","n_go"):
 k=L/"out/kit_n_go" if name=="n_go" else L/"work/build24/kits"/name
 for p in sorted((k/"k").glob("*.json")):
  scan(json.loads(p.read_text()),name+"/k/"+p.name)
for h,v in ups.items():pending.append(dict(kind="pin",where="upload/"+h,path=v["local_path"],sha256=h))
while pending:
 r=pending.pop();h=r["sha256"]
 if h in seen:continue
 seen.add(h);p=Path(ups[h]["local_path"]) if h in ups else Path(r["path"])
 if not str(p).startswith("/scratch/jjyeung/") or not p.is_file() or p.stat().st_size>20_000_000 or p.suffix in (".sqlite",".db",".pt",".bin",".npz"):continue
 if J.sha(p)!=h:continue
 if h not in ups:
  target=D/"pins"/h;shutil.copyfile(p,target);v=dict(local_path=str(target),opaque_name="u/"+h,sha256=h,bytes=target.stat().st_size);c["added"][h]=v;ups[h]=v
 try:scan(J.load(p),"u/"+h)
 except (ValueError,UnicodeError):pass
c["host_pins"]={h:host[h] for h in c["host_pins"]};J.write(D/"CLOSURE.json",c)
for r in records:
 h=r.get("sha256")
 if h in ups:r["resolution"]="staged u/"+h
 elif h in host:r["resolution"]="authenticated production staging: "+host[h]
 elif r["path"].startswith("/tmp/"):r["resolution"]="node-local generated path"
 elif r["where"].startswith(("q/k/l.json","n/k/l.json","n_go/k/l.json")):r["resolution"]="authenticated donor staging map; pool source or job destination"
 elif r["path"].startswith(("/scratch/fsw/","/lustre/","/project/")):r["resolution"]="production staging or immutable provenance; native host path"
 else:r["resolution"]="requires classification"
J.write(D/"PATH_INVENTORY.json",dict(records=records,unique_pin_hashes=len(seen),added_files=len(c["added"]),added_bytes=sum(v["bytes"] for v in c["added"].values()),host_pins=c["host_pins"]))
print("records",len(records),"pins",len(seen),"added",len(c["added"]),sum(v["bytes"] for v in c["added"].values()),"host",c["host_pins"])
print("unclassified",len([r for r in records if r["resolution"]=="requires classification"]))
