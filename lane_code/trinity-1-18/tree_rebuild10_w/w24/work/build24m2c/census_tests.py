from common import *
import sqlite3,copy,time
sys.path[:0]=[str(kit("q")/"b")]
import sv
from student_pilot.r1_persisted import scope
from student_pilot.r1_rooms import Rooms
from student_pilot.s1_exclusions import dev_names,benchmark_names
from student_pilot.r2_withheld import Withheld
from student_pilot.carrier_c1_routing import load_exclusions
from student_pilot.p3_provenance import file_pin
F=D/"census";F.mkdir(exist_ok=True)
paths={v["sha256"]:v["local_path"] for v in J.load(D/"UPLOADS_q.json")["files"] if v["opaque_name"].startswith("u/")}
cfg=J.load(kit("q")/"k/n.json")
scene=L/"work/build24m2b/scene_tests/p/i/sc/sc";receipt=J.load(scene/"2.json")
cfg.update(r2_scene_rebuild=file_pin(scene/"2.json"),scene_coverage=receipt["scene_coverage"])
for p in scene.rglob("*"):
 if p.is_file():paths[J.sha(p)]=str(p)
with scope(paths):
 rooms=Rooms(cfg["r1_training"]["room_authority"]);classify=sv.classifier(cfg)
 # Exact pointing canonical field and native room function from audit_point.py.
 point=json.loads(Path("/scratch/jjyeung/orch_n30/fb_pack/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl").read_text().splitlines()[0])
 prow=dict(qid=point["row_key"],provenance=dict(canonical_scene=point["canonical"]))
 assert rooms.canonical(prow)[0] is None and classify(prow,"pointing")["K1_heldout"]
 candidates={"K1_heldout":[point["canonical"]],"R0":sorted(rooms.r0),"withheld":sorted(Withheld().aliases),
 "benchmark":benchmark_names(cfg["benchmark_scene_exclusions"]),"dev":dev_names(cfg["dev_scene_exclusions"]),"official":sorted(load_exclusions(cfg["exclusions"]))}
 selected={}
 for status,names in candidates.items():
  for name in names:
   if name.startswith("scannet/scene") and "_" not in name:name+="_00"
   if name.startswith("d1/scene") and "_" not in name:name+="_00"
   row=dict(qid="hit",dataset=name.split("/")[0],scene=name.split("/",1)[1])
   try:flags=classify(row,"vqa")
   except ValueError:continue
   if flags[status]:selected[status]=row;break
  assert status in selected,status
 clean=dict(qid="clean",canonical="scannet/scene9999_00",target="<think>synthetic</think>A")
 assert not any(classify(clean,"vqa").values())
 records=[]
 for case in ["clean"]+[s+"_"+flag for s in ("pose","vqa","routing","pointing") for flag in sv.STATUSES]:
  root=F/case;root.mkdir();node=root/"node";node.mkdir();k=root/"kit";(k/"k").mkdir(parents=True)
  J.write(k/"k/p.json",dict(n_root=str(root/"target")))
  prep={"streams":{}}
  wanted=None if case=="clean" else next((s,flag) for s in ("pose","vqa","routing","pointing") for flag in sv.STATUSES if case==s+"_"+flag)
  for stream in ("pose","vqa","routing","pointing"):
   rows=[dict(clean,qid=stream+"_clean")]
   if wanted and wanted[0]==stream:
    hit=dict(selected[wanted[1]],qid=stream+"_hit")
    if stream=="pointing" and wanted[1]=="K1_heldout":hit=prow
    rows.append(hit)
   db=root/(stream+".sqlite")
   with sqlite3.connect(db) as con:
    con.execute("create table rows(i integer primary key,row text,target text)")
    for i,row in enumerate(rows):con.execute("insert into rows values(?,?,?)",(i,json.dumps(row),"{}"))
   prep["streams"][stream]=dict(database=file_pin(db),count=len(rows))
  c=copy.deepcopy(cfg);c["preparation"]=J.write(root/"prep.json",prep)
  error=None
  try:sv.publish(k,node,c,"91")
  except ValueError as e:error=str(e)
  live=root/"target/o/91/live";v=J.load(live/"s2.json");hits=J.load(live/"s3.json")
  if wanted:
   assert error=="R1_SCENE_PROTECTED_ADMITTED_ROWS",(case,error)
   assert v["counts"][wanted[0]][wanted[1]]>0 and hits[wanted[0]],case
  else:
   assert error is None,error
   assert all(x["admitted"]==1 and not any(x[s] for s in sv.STATUSES) for x in v["counts"].values())
  assert not (live/"WAITING_REVIEW.json").exists()
  assert sum(p.stat().st_size for p in live.iterdir())<1_000_000
  records.append(dict(case=case,refusal=error,counts=v["counts"],bytes=sum(p.stat().st_size for p in live.iterdir())))
J.write(D/"CENSUS_TESTS.json",dict(status="PASS",native_readers=True,pointing_canonical_scene=True,records=records))
print("25 native census cases PASS")
