from common import *
from copy import deepcopy
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest,file_pin
from student_pilot.r1_persisted import scope
from student_pilot.r1_launch22 import validate_removals
from student_pilot.r1_coverage import verify_union
from student_pilot.r1_rooms import V7_K1_LIST,N_LIST
from student_pilot.row_removals import Removals
from student_pilot.s1_exclusions import Exclusions
actual=inventory(T);expected=J.load(L/"work/build24m2/TREE24L3_SEAL.json")
assert actual==expected["files"]
ledger=J.load(L/"work/build24m2/UNCHANGED24L3.json")
for n,v in ledger["files"].items():assert actual.get(n)==v["after"],n
J.write(D/"TREE_VERIFICATION.json",dict(status="PASS",tree_sha256=digest(actual),files=len(actual),prior_fuzz0_patch=J.load(L/"work/build24m2/TREE_VERIFICATION.json")))
paths={v["sha256"]:v["local_path"] for v in J.load(L/"work/build24m1/UPLOADS_q.json")["files"] if v["opaque_name"].startswith("u/")}
source=L.parent.parent/"fb_pack/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl"
source=Path("/scratch/jjyeung/orch_n30/fb_pack/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl")
assert J.sha(source)=="d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1"
assert J.sha(source.with_name("audit_point.py")).startswith("6035517f")
assert J.sha(source.with_name("AUDIT_POINTING_K1.json")).startswith("8d5c1a9a")
rows=[json.loads(s) for s in source.read_text().splitlines()];assert len(rows)==320
records={}
with scope(paths):
 for name in ("q","n","n_go","qd"):
  cfg=J.load(kit(name)/"k/n.json");validate_removals(cfg)
  before=deepcopy(cfg["remove_files"]);test=deepcopy(cfg);test["remove_files"].append(file_pin(source))
  try:validate_removals(test)
  except ValueError as e:refusal=str(e)
  else:raise AssertionError("13th list accepted unexpectedly")
  assert refusal=="R1_NAMING_REMOVAL_ORDER"
  union=verify_union(test["r1_training"],test["remove_files"],V7_K1_LIST,N_LIST)
  old=Removals(before);new=Removals(test["remove_files"]);rule=Exclusions(cfg["dev_scene_exclusions"],cfg["benchmark_scene_exclusions"])
  for entry in rows:
   row=dict(qid=entry["row_key"],canonical=entry["canonical"],provenance=dict(canonical_scene=entry["canonical"]))
   assert old.keep(row);assert not new.keep(row)
   rule.keep(row,"pointing")
  assert new.removed==[0]*12+[320] and before==cfg["remove_files"]
  records[name]=dict(status="STOPPED",refusal=refusal,verify_union=union,plain_pin=file_pin(source),fixture_removals=new.removed,existing_12_unchanged=True)
J.write(D/"POINTING_REMOVAL_TESTS.json",dict(status="STOPPED_BY_TREE_GATE",kits=records,production_expected=dict(source=25020,new_removed=320,existing_removed=0,scene_excluded=6584,k1_admitted_after_new_list=0),production_counts_source="Supplied audit only; production database not read"))
replace(L/"out/POINTING_REMOVAL_BLOCKER.md","Item 2c is stopped. The sealed r1_launch22.validate_removals requires tuple(actual) == REMOVAL_ORDER (exactly 12 pins), actual == launch22.removal_order, and NAMING_REMOVE last. Appending the authenticated plain pin d21e374f raises R1_NAMING_REMOVAL_ORDER in all four kits. verify_union accepts the appended pin but cannot bypass validate_removals. No list or gate was changed. The native Removals fixture removes all 320 listed keys with the candidate plain pin and removes none through the existing 12 lists. Production counts are supplied audit expectations, not a local production scan.\n")
print("tree and removal blocker verified")
