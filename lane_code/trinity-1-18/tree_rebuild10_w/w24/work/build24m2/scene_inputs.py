from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];T=L/"work/tree_r1";D=L/"work/build24m2";sys.path.insert(0,str(L/"work/build24"));import joblib as J
k=L/"work/build24/kits/q";c=J.load(k/"k/n.json");s=J.load(k/"k/p.json")
up={x["sha256"]:x for x in J.load(L/"work/build24m1/UPLOADS_q.json")["files"] if x["opaque_name"].startswith("u/")};pins={x["sha256"] for x in s["uploads"]};rows=[]
def add(name,pin,reader,role="native rebuild"):
 h=pin["sha256"];v=up.get(h);ok=h in pins and bool(v)
 if v:assert J.sha(v["local_path"])==h
 rows.append(dict(input=name,sha256=h,path=pin["path"],authenticated_u=ok,reader=reader,role=role,local_path=v["local_path"] if v else None))
 try:return J.load(v["local_path"]) if v else None
 except ValueError:return None
add("benchmark scenes",c["benchmark_scene_exclusions"],"Exclusions/benchmark_names")
add("merged dev exclusions",c["dev_scene_exclusions"],"require_merged/Exclusions/dev_names")
for key,pin in c["r1_training"]["room_authority"].items():add("room authority "+key,pin,"r1_rooms.Rooms", "R0/K1 census; rebuild itself does not read this authority")
p=T/"student_pilot/r2_withheld.json";add("withheld-80",dict(path=str(p),sha256=J.sha(p)),"Withheld() default reads sealed source-relative file")
add("K1 scene division",c["scene_division"],"native preparation", "census; rebuild itself does not read scene_division")
pose=add("pose mix",c["streams"]["pose"],"resolve five source receipts")
sourcepins={"vqa":c["streams"]["vqa"],"camera":c["streams"]["routing"],"pointing":c["streams"]["pointing"]}
for name,source in zip(("pose_a2v3","pose_a3v2"),pose["sources"]):sourcepins[name]=source["receipt"]
for name,pin in sourcepins.items():
 v=add("source receipt "+name,pin,"rebuild_receipt/load/pinned")
 if v is None:
  # Named external receipt replicas are available in the inherited host mapping.
  source=s.get("host_paths",{}).get(pin["sha256"])
  if source and Path(source).is_file():v=J.load(source)
 if v:
  rp=v.get("rows_metadata",v.get("database"))
  if rp:add("source population "+name,rp,"rows()/sqlite or JSON lines")
  else:rows.append(dict(input="source population "+name,sha256="UNRESOLVED",path=pin["path"],authenticated_u=False,reader="source receipt unavailable"))
pool=add("pool selection evidence",c["s1_routing"]["selection"],"select authenticated pool manifest")
for label in ("manifest","tokenizer"):
 pin=pool.get(label)
 if pin:
  v=add("pool "+label,pin,"rebuild_pool/Pool/prepare")
  if label=="manifest" and v:
   for name in ("dev_s1","eval_rooms","room_release_gate"):
    entry=v["exclusions"][name]
    add("pool exclusion "+name,dict(path=entry["list"],sha256=entry["list_sha256"]),"Pool")
    for pkey in ("withhold","v2"):
     if pkey in entry:add("pool "+pkey,dict(path=entry[pkey],sha256=entry[pkey+"_sha256"]),"Pool.scenes")
   for entry in v["sets"]:
    kind="packed" if "packed" in entry["files"] else "rows";pin=entry["files"][kind]
    add("pool rows "+entry["name"],{x:pin[x] for x in ("path","sha256")},"rebuild_pool/rows")
for i,pin in enumerate(c["remove_files"]):add("removal "+str(i),pin,"rebuild_pool/prepare/Removals")
missing=[r for r in rows if not r["authenticated_u"]]
J.write(D/"SCENE_REBUILD_INPUTS.json",dict(status="STOPPED" if missing else "READY",inputs=rows,missing=missing))
lines=["Item 2b is stopped: the required input set is not entirely authenticated under the existing planner-staged u/<sha256> contract.","", "The native rebuild reads dev/benchmark lists, the sealed withheld-80 file, five source receipts and their full metadata populations, the pool manifest, its exclusion lists and populations, removals and optional tokenizer. R0/K1 authorities are needed for the requested census; rebuild does not consume them directly.","", "| Input | SHA256 | Already authenticated u/ input | Reader / role |", "| --- | --- | --- | --- |"]
for r in rows:lines.append("| "+r["input"]+" | "+r["sha256"]+" | "+("yes" if r["authenticated_u"] else "no")+" | "+r["reader"]+" |")
lines += ["", "The withheld-80 bytes are authenticated by the sealed source archive, but no k/*.json pin stages them as u/<sha256> through the planner. Production database pins may be authenticated by stream closure on Orchard; that differs from an already uploaded u/ input. Missing source metadata is not supplied from synthetic fixtures.","", "No rebuild wrapper, receipt, census, verifier change or gate change is installed. The existing native verification remains active. The orchestrator must resolve the missing-input contract before item 2b can be built."]
(L/"out/SCENE_REBUILD_INPUTS.md").write_text("\n".join(lines)+"\n")
print("STOPPED",len(missing),"of",len(rows),"not uploaded/staged u inputs")
for r in missing:print(r["input"],r["sha256"])
