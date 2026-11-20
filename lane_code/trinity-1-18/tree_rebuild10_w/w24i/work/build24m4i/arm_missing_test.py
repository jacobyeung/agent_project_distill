from pathlib import Path
from common import *
from support import cap as putcap,reseal as seal_new
import shutil
F=D/"arming_final";record=J.load(D/"ARM_TESTS.json")["records"][0];dh=record["staged_member"].split("/")[1]
origin=F/"plan_kit_q";k=F/"missing_db_kit"
for p in origin.rglob("*"):
    if not p.is_file():continue
    rel=p.relative_to(origin);q=k/rel;q.parent.mkdir(parents=True,exist_ok=True)
    if str(rel) in ("k/p.json","BUILD.json","SHA256SUMS.txt"):shutil.copyfile(p,q)
    else:os.link(p,q)
p=J.load(k/"k/p.json");p["uploads"]=[x for x in p["uploads"] if x["sha256"]!=dh];p["pin_paths"].pop(dh);putcap(k/"k/p.json",p);seal_new(k)
sys.path.insert(0,str(k/"b"));import pl
base=J.load(F/"routing_selection.json")["inputs_pinned"]["routing_base"]
manifest=J.load(F/"handover_q.json")["pins"]["full_weights"]
index=dict(path=str(F/"index_q.json"),sha256=J.sha(F/"index_q.json"))
handover=dict(path=str(F/"handover_q.json"),sha256=J.sha(F/"handover_q.json"),bytes=(F/"handover_q.json").stat().st_size)
small={v["sha256"]:dict(path=v["path"],sha256=v["sha256"],bytes=Path(v["path"]).stat().st_size) for v in (index,manifest)}
r=dict(kit_sha256=J.seal(k),archive=None,small_files=small,receipt=handover,config=dict(streams=dict(routing=base),r1_training=dict(persisted_files={})),request=dict(routing_base=base),paths={},tar_sha256="0"*64,tar_bytes=0,parts=[])
root=F/"missing_db_node";root.mkdir()
try:pl.plan_payload(k,r,root,regeneration=False)
except ValueError as e:
    assert str(e)=="R1_STAGED_PIN_MISSING:"+dh+":config.streams.routing.database",str(e)
    J.write(D/"ARM_MISSING_DB_TEST.json",dict(status="PASS",refusal=str(e),scope="Selection present, database bytes present at Orchard stand-in, but database omitted from authenticated staging inventory; actual unchanged q planner refuses."))
else:raise AssertionError("unstaged database accepted")
print("Missing DB inventory refuses; fixed armed q plan passed",flush=True)
