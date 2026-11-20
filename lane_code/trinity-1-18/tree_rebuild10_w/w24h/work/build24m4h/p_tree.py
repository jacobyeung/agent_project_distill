from pathlib import Path
import sys,json,hashlib,shutil,tarfile,io,os
L=Path(__file__).resolve().parents[2];W=L.parent;D=L/"work/build24m4h"
v=json.loads((W/"ext/pwrap/k/7.json").read_text());loc=json.loads((D/"TREE_LOCATIONS.json").read_text());root=D/"p_tree";root.mkdir()
for n,h in v["files"].items():
 src=Path(loc["found"][n]);raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()==h
 dst=root/n;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw);dst.chmod(src.stat().st_mode&511)
sys.path.insert(0,str(root))
from student_pilot.s1_pool import implementation
s=json.loads((W/"w24g/work/build24m4g/inputs/5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af").read_text())
a=implementation();diff={k:[s["implementation"].get(k),a.get(k)] for k in set(a)|set(s["implementation"]) if s["implementation"].get(k)!=a.get(k)}
print("IMPLEMENTATION",len(a),len(s["implementation"]),"DIFF",json.dumps(diff))
from student_pilot.source_seal import inventory,archive
from student_pilot.p3_provenance import digest,sha256
assert inventory(root)==v["files"]
print("TREE",digest(inventory(root)))
archive(root,D/"p.tar",v["files"])
print("ARCHIVE",sha256(D/"p.tar"),"EXPECTED",v["archive"]["sha256"])
(D/"P_GUARD.json").write_text(json.dumps(dict(implementation_entries=len(a),differences=diff,tree=digest(inventory(root)),archive=sha256(D/"p.tar")),indent=2)+"\n")
