from pathlib import Path
import sys,base64,json,re,gzip,hashlib,collections
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";sys.path.insert(0,str(L/"work/build24"));import joblib as J
closure=J.load(D/"CLOSURE.json");rows=[];summaries={}
for name in ("q","n","n_go"):
 k=L/"out/kit_n_go" if name=="n_go" else L/"work/build24/kits"/name
 spec=J.load(k/"k/p.json");uploads={x["sha256"] for x in spec["uploads"]};kitsha={J.sha(p):str(p.relative_to(k)) for p in k.rglob("*") if p.is_file()}
 def walk(v,where):
  if isinstance(v,dict):
   if v.get("encoding") in ("base64-json","base64") and "payload" in v:
    raw=base64.b64decode(v["payload"]);assert hashlib.sha256(raw).hexdigest()==v["sha256"]
    try:walk(json.loads(raw),where+".$decoded")
    except (ValueError,UnicodeError):pass
   if "path" in v and "sha256" in v:
    h=v["sha256"];p=v["path"]
    if h in uploads:resolution="u/"+h;mechanism="upload and r1_persisted.scope"
    elif h in spec.get("host_paths",{}):resolution=spec["host_paths"][h];mechanism="authenticated donor staged database; r1_persisted.scope"
    elif h in kitsha:resolution=kitsha[h];mechanism="sealed kit member"
    else:resolution=p;mechanism="donor transport, generated output, or host input; preserved native path"
    rows.append(dict(kit=name,kind="pin",where=where,path=p,sha256=h,localized=resolution,mechanism=mechanism))
   for key,x in v.items():
    if key!="payload":walk(x,where+"."+key)
  elif isinstance(v,list):
   for i,x in enumerate(v):walk(x,where+"."+str(i))
  elif isinstance(v,str) and v.startswith("/"):
   rows.append(dict(kit=name,kind="absolute_string",where=where,path=v))
 for p in sorted((k/"k").glob("*.json")):walk(json.loads(p.read_text()),"k/"+p.name)
 active=[]
 for fn in ("c.json","n.json","r.json","h.json"):
  def local(v,where):
   if isinstance(v,dict):
    for key,x in v.items():local(x,where+"."+key)
   elif isinstance(v,list):
    for i,x in enumerate(v):local(x,where+"."+str(i))
   elif isinstance(v,str) and v.startswith(("/scratch/jjyeung/","/home/","/data/","/data2/","/data3/")):active.append(dict(field=where,path=v))
  local(J.load(k/"k"/fn),fn)
 assert not active,(name,active)
 summaries[name]=dict(kit_seal=J.seal(k),trinity_absolute_paths_in_active_configs=active,uploaded_pins=len(uploads),host_pins=spec.get("host_paths",{}))
for name in ("q","n"):
 for v in J.load(D/("UPLOADS_"+name+".json"))["files"]:
  if v["opaque_name"].startswith("u/"):assert J.sha(v["local_path"])==v["sha256"]
raw=json.dumps(dict(records=rows,kits=summaries),sort_keys=True,separators=(",",":")).encode()
(D/"DECODED_PATHS.json.gz").write_bytes(gzip.compress(raw,6,mtime=0))
J.write(D/"PATH_CLOSURE.json",dict(status="PASS_ACTIVE_KIT_PATHS",kits=summaries,records=len(rows),inventory="DECODED_PATHS.json.gz",nested_referenced_content_inventory="PATH_INVENTORY.json.gz",missing_added=closure["added"],unchanged_transports="Existing k/l.json and donor receipt transports supply production weights, stores, frame packages and catalog payloads. Their original provenance strings are authenticated content; they are not rewritten.",tree_requires_trinity_paths=False,limitations="The local stand-in does not contain production routing payloads or complete production stores. Their bytes and transitive frame access cannot be proved here."))
print("PASS",len(rows),"decoded records; no Trinity paths in active c/n/r/h")
