from common import *
from student_pilot.source_seal import inventory,archive,create,check_archive
from student_pilot.p3_provenance import digest,source_files,file_pin
files=inventory(T);tree=digest(files);target=D/("t_"+tree[:16]+".tar")
archive(T,target,files,compress=True);check_archive(file_pin(target),files)
closure={str(p.relative_to(T)):J.sha(p) for p in source_files([T/"student_pilot/carrier_c1_run.py"])}
for name in ("q","n","n_go","qd"):
 k=kit(name);control=J.load(k/"k/a.json");spec=J.load(k/"k/p.json");ns=spec["namespace"]+"/p/q"
 replace(k/control["source"]["path"],target.read_bytes())
 control["source"].update(sha256=J.sha(target),tree_sha256=tree);cap(k,"k/a.json",control)
 cap(k,"k/7.json",dict(schema="c1-sealed-source-v1",commit="sha256:"+tree,tree_sha256=tree,files=files,archive={x:control["source"][x] for x in ("path","sha256")},sources=closure,operation_sources=closure))
 code=create(T,target,closure,{},archive_path=ns+"/t.tar");raw=(json.dumps(code,sort_keys=True,indent=2)+"\n").encode();cap(k,"k/c0.json",raw)
 old=spec["code_sha256"];spec["code_sha256"]=hashlib.sha256(raw).hexdigest()
 # The runtime resolver obtains the decoded code capsule via the shared upload inventory.
 for item in spec["uploads"]:
  if item["sha256"]==old:
   item["sha256"]=spec["code_sha256"];item["bytes"]=len(raw)
   for key in ("path","opaque_name","name"):
    if key in item:item[key]=item[key].replace(old,spec["code_sha256"])
 spec["pin_paths"]={v["sha256"]:spec["namespace"]+"/u/"+v["sha256"] for v in spec["uploads"]}
 cap(k,"k/p.json",spec)
 cfg=J.load(k/"k/c.json");cfg["code"]=dict(path="k/7.json",sha256=J.sha(k/"k/7.json"));cap(k,"k/c.json",cfg)
 cfg=J.load(k/"k/n.json")
 if "code" in cfg:cfg["code"]=dict(path="u/"+spec["code_sha256"],sha256=spec["code_sha256"]);cap(k,"k/n.json",cfg)
 dest=D/"u"/spec["code_sha256"];dest.parent.mkdir(exist_ok=True)
 if not dest.exists():dest.write_bytes(raw)
 build=J.load(k/"BUILD.json");build["source_seal"]=tree;cap(k,"BUILD.json",build)
 replace(k/"SHA256SUMS.txt",(k/"SHA256SUMS.txt").read_bytes());print(name,reseal(k))
replace(L/"out/TREE_SEAL.json",json.dumps(dict(tree_sha256=tree,files=len(files)),indent=2)+"\n")
replace(L/"out/TREE_FILES.sha256","".join(h+"  "+n+"\n" for n,h in sorted(files.items())))
