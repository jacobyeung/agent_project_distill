import sys,copy
from pathlib import Path
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from launch_r1.build import verify
from student_pilot.carrier_c1_run import identity
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
expected=dict(q="d54120b4",n="fec34c9d",n_go="60d24119",qd="62d8a7f5")
base={n:{str(f.relative_to(kit(n))):dict(sha256=J.sha(f),bytes=f.stat().st_size,mode=f.stat().st_mode&511) for f in kit(n).rglob("*") if f.is_file()} for n in NAMES}
assert all(verify(kit(n)).startswith(expected[n]) for n in NAMES)
assert digest(inventory(T))=="0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de"
J.write(D/"ORIGINAL_KITS.json",base)
J.write(D/"BASE_SEALS.json",{n:verify(kit(n)) for n in NAMES})
cfg=J.load(kit("n")/"k/c.json");old=cfg["r2_sampling"]
card=J.load(input_file(old["card"]["sha256"]));previous=copy.deepcopy(card)
p=J.load(D/"P_CONFIG.json");rate=Fraction(p["type_mix"]["streams"]["vqa"]["cells"]["room"]["cents"],100)
assert rate==Fraction(17,10)
for cell in card["cells"]:
 if cell["type"]=="room_size":assert cell["rows_per_step"]==0;cell["rows_per_step"]=float(rate)
 if cell["type"]=="direction":cell["rows_per_step"]=float(Fraction(str(cell["rows_per_step"]))-rate)
card["room_rows_per_step"]=float(rate)
assert sum(Fraction(str(c["rows_per_step"])) for c in card["cells"] if c["stream"]=="vqa")==128
newcard=save_input(card)
pop=J.load(input_file(old["population"]["sha256"]));pop["card_sha256"]=newcard["sha256"]
for pin in pop["evidence"]:
 if pin["sha256"]==old["card"]["sha256"]:pin.update(newcard)
newpop=save_input(pop)
indices=J.load(input_file(old["indices"]["sha256"]));indices["population_sha256"]=newpop["sha256"]
newindices=save_input(indices)
new=dict(card=newcard,population=newpop,indices=newindices)
replacements={old[key]["sha256"]:pin["sha256"] for key,pin in new.items()}
def refs(v):
 if isinstance(v,dict):return {refs(k):refs(x) for k,x in v.items()}
 if isinstance(v,list):return [refs(x) for x in v]
 if isinstance(v,str):
  for a,b in replacements.items():v=v.replace(a,b)
 return v
identities={}
for n in NAMES:
 k=kit(n);identities[n]={}
 for rel in ("k/c.json","k/n.json","k/8.json"):
  before=J.load(k/rel);after=refs(before);cap(k/rel,after)
  if rel!="k/8.json":identities[n][rel]=dict(before=identity(before),after=identity(after),before_payload_sha256=J.load_raw(L/"attic/build24m4i"/k.relative_to(L)/rel)["sha256"],payload_sha256=J.load_raw(k/rel)["sha256"],file_sha256=J.sha(k/rel))
 spec=J.load(k/"k/p.json")
 for pin in new.values():
  h=pin["sha256"];spec["uploads"].append(dict(sha256=h,bytes=input_file(h).stat().st_size,opaque_name="u/"+h));spec["pin_paths"][h]=spec["namespace"]+"/u/"+h
 spec["uploads"].sort(key=lambda x:x["sha256"]);cap(k/"k/p.json",spec)
 s=J.load(k/"k/s.json");entry=s["entries"].pop(old["card"]["path"]);raw=input_file(newcard["sha256"]).read_bytes()
 s["entries"][newcard["path"]]=dict(payload=base64.b64encode(raw).decode(),sha256=newcard["sha256"]);cap(k/"k/s.json",s)
seals={n:reseal(kit(n)) for n in NAMES}
J.write(D/"SEALS.json",seals);J.write(D/"CONFIG_IDENTITIES.json",identities)
J.write(D/"CONFIG_DELTA.json",dict(case="b",ruling="ORCH 0511Z",before=old,after=new,hash_replacements=replacements,card_before=previous,card_after=card,draw_changes={"room_size":[0,1.7],"direction":[36.866,35.166],"room_rows_per_step":[0,1.7]},annotation="room_rule is inert text, retained byte-for-byte to restrict the config diff to draw entries and dependent identities; its zero-until-audit statement does not describe executable behavior."))
print("SEALS",seals);print("NEW_CARD",newcard);print("N_GO",identities["n_go"]["k/c.json"])
