from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import json,sys,shutil,hashlib
L=Path(__file__).resolve().parents[2];B=L/"work/build21";D=L/"work/build23b";A=L/"attic/build23b";T=L/"work/tree_r1";K=B/"kits/q"
sys.path[:0]=[str(T),str(B)]
import joblib as J
from student_pilot.p3_provenance import load,pinned,file_pin
from student_pilot.r1_persisted import scope
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1 import production_proof as Q
assert digest(inventory(T)).startswith("b4edc475")
for name in ("UPLOADS.json","PACKAGE_MANIFEST.json","FINAL_KITS.json","naming21.py"):
 shutil.copyfile(B/name,A/name)
shutil.copytree(K,A/"q")
for name in ("student_pilot/r1_coverage.py","student_pilot/r1_population.py","student_pilot/r1_rooms.py","student_pilot/s1_admission.py","launch_r1/build.py","launch_r1/entry.py","launch_r1/production_proof.py"):
 p=A/"tree"/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(T/name,p)
for name in ("MINIMAL_TREE.patch","MINIMAL_MERGE_NOTES.md","TREE_SEAL.json","TREE_FILES.sha256"):
 shutil.copyfile(L/"out"/name,A/name)
uploads=load(B/"UPLOADS.json");paths={x["sha256"]:x["local_path"] for x in uploads["files"]}
cfg=load(K/"k/n.json");request=load(K/"k/r.json")
with scope(paths):
 sources=load(pinned(cfg["r1_training"]["row_sources"]))
 cfg["r1_training"]["row_slice_inputs"]={"recovery":sources["recovery"]["source"]}
 J.write(D/"before_config.json",cfg);request.update(config=file_pin(D/"before_config.json"),staged_pins=[],room_audit=cfg["r1_training"]["room_audit"])
 # Only output writes and staging list (empty, as no external staging occurs) are adapted.
 request["staged_pins"]=[request["config"]]
 result=Q._run(request,D/"before")
 assert result["refusal"]=="ValueError:R1_PROOF_FRAME_HOST_REQUIRED",result
 J.write(D/"BEFORE.json",dict(tree=digest(inventory(T)),kit=J.seal(K),mutation="r1_training.row_slice_inputs.recovery",result=result))
 J.write(D/"SOURCE_FIELDS.json",dict(row_sources=list(sources),membership=list(load(pinned(cfg["r1_training"]["source_membership"]))["sources"])))
print(json.dumps(result))
