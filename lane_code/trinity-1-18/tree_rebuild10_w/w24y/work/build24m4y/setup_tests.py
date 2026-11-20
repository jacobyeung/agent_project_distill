from pathlib import Path
import json,shutil,os
L=Path.cwd();D=L/"work/build24m4y";V=L.parent/"w24v/work/build24m4v";U=L/"work/build24m4u"
for p in V.glob("*.py"):
 if p.name in ("setup_tests.py","preflight.py"):continue
 text=p.read_text().replace(str(L.parent/"w24v"),str(L)).replace("build24m4v","build24m4y")
 text=text.replace("attic/build24m4y/work/tree_r1c","attic/build24m4v_apply/work/tree_r1c")
 if p.name=="tree_tests.py":
  text=text.replace("/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/fixtures",str(D/"tmp/fixtures")).replace("/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21",str(D))
 (D/p.name).write_text(text)
for n in ("new_tests.py","publication_tests.py","live_tests.py","publication_integration.py","bind_tests.py"):
 text=(U/n).read_text().replace(str(L.parent/"w24u"),str(L)).replace("build24m4u","build24m4y")
 text=text.replace("attic/build24m4y/","attic/build24m4u/").replace("R=L.parent/work/d173725/173725","R=L/work/build24m4u/real173725")
 (D/n).write_text(text)
records=[]
for n in ("inputs","scanners","proofs","published"):
 for p in (V/n).rglob("*"):
  if p.is_file():
   q=D/p.relative_to(V);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);q.chmod(p.stat().st_mode&511);records.append((str(q.relative_to(D)),p.stat().st_size))
for n in ("ARM_BASE_FILES.json","ARM_BASE_SEALS.json","SOURCES.json","BEFORE.json","pool_row.json","a0_units_row.json","a0_recovery_row.json","a0_pool_abs_distance_reworded_row.json","c072905b.json"):
 shutil.copyfile(V/n,D/n)
shutil.copyfile(U/"EXTENT_EVIDENCE.json",D/"EXTENT_EVIDENCE.json")
shutil.copytree(U/"observations",D/"observations")
shutil.copyfile(L/"work/build24m4v_apply/RESULT.json",D/"APPLY_RESULT.json")
(D/"SEALS.json").write_text(json.dumps(json.loads((V/"SEALS.json").read_text()),indent=2)+"\n")
# Keep source proof and report local. These names are not upload destinations.
for n in ("TREE_CHANGE_24M4V.patch","TREE_T_24M4V.md"):
 shutil.copyfile(V.parents[1]/"out"/n,D/n)
print(json.dumps(dict(fixture_files=len(records),fixture_bytes=sum(v[1] for v in records))))
