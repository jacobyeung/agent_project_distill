from pathlib import Path
from pathlib import Path
import sys,json,base64,hashlib,os
L=Path(__file__).resolve().parents[2];D=L/"work/build24m4w"
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24w/work/tree_r1c']
import joblib as J
def kit(name):return L/("out/kit_n_go" if name=="n_go" else "out/kit_qd" if name=="qd" else "work/build24/kits/"+name)

from support import cap as capsule_write,reseal as seal_new
import sqlite3,copy,shutil,importlib.util
from unittest.mock import patch
F=D/"arming_final";F.mkdir()
spec=importlib.util.spec_from_file_location("arm",D/"arm_fixture.py");arm=importlib.util.module_from_spec(spec);spec.loader.exec_module(arm)
def clone(origin,target,change):
    for p in origin.rglob("*"):
        if not p.is_file():continue
        rel=p.relative_to(origin);q=target/rel;q.parent.mkdir(parents=True,exist_ok=True)
        if str(rel) in change:shutil.copyfile(p,q);q.chmod(p.stat().st_mode&511)
        else:os.link(p,q)
fixture_root=F/"workspace";fixture_root.mkdir();staged=F/"staged/u";staged.mkdir(parents=True)
db=F/"fixture.sqlite"
with sqlite3.connect(db) as c:
    c.execute("CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)")
    c.execute("INSERT INTO rows VALUES(0,?,?)",(json.dumps(dict(qid="fixture",canonical="scannet/scene9999_00")),"{}"))
dh=J.sha(db);size=db.stat().st_size;os.link(db,staged/dh)
base=J.write(F/"base.json",dict(database=dict(path="u/"+dh,sha256=dh),count=1))
bh=base["sha256"];os.link(F/"base.json",staged/bh)
selection=J.write(F/"routing_selection.json",dict(regenerated_sha256=dh,rows=1,row_id_digest=hashlib.sha256(b"fixture").hexdigest(),logical_output="/tmp/q_22c714e1/p/q/selection",inputs_pinned=dict(routing_base=dict(path="u/"+bh,sha256=bh),routing_database=dict(path="u/"+dh,sha256=dh))))
meta=J.write(F/"db_bytes.json",dict(files=[dict(path="o/1/p/q/selection/rows.sqlite",sha256=dh,size=size)]))
for name in ("q","n","n_go"):
    origin=kit(name);target=fixture_root/("out/kit_n_go" if name=="n_go" else "work/build24/kits/"+name)
    clone(origin,target,{"k/p.json","BUILD.json","SHA256SUMS.txt"})
    p=J.load(target/"k/p.json");p["uploads"].append(dict(sha256=bh,bytes=(F/"base.json").stat().st_size));p["pin_paths"][bh]=p["namespace"]+"/u/"+bh
    capsule_write(target/"k/p.json",p);seal_new(target)
review=F/"REVIEW_RESULT.txt"
review.write_text("Synthetic test verdict only: PASS\n"+selection["sha256"]+"\n"+dh+"\n")
auth=dict(reviewed_selection_sha256=selection["sha256"],reviewed_regenerated_sha256=dh,review_verdict=review)
with patch.object(arm,"L",fixture_root):
    result=arm.apply(F/"routing_selection.json",F/"db_bytes.json",fixture_root/"out/armed",base_path=F/"base.json",**auth)
assert result["already_staged"][0]["sha256"]==dh
config=fixture_root/"out/armed/kits/n_go/k/c.json"
assert result["armed_n_go_config"]["file_sha256"]==J.sha(config)
assert result["armed_n_go_config"]["payload_sha256"]==hashlib.sha256(base64.b64decode(json.loads(config.read_text())["payload"])).hexdigest()
assert result["review"]["verdict"]["sha256"]==J.sha(review)
for name,seal in result["kits"].items():assert J.seal(fixture_root/"out/armed/kits"/name)==seal
assert not any(r["name"]=="u/"+dh or r["name"].startswith("n_go/") for r in result["files"])
assert (fixture_root/"out/armed/upload/u"/selection["sha256"]).read_bytes()==(F/"routing_selection.json").read_bytes()
os.link(F/"routing_selection.json",staged/selection["sha256"])
checks=[]
for name in ("q","n","n_go"):
    armed=fixture_root/"out/armed/kits"/name
    # Compact authenticated staging fixture: only unrelated production payloads
    # are replaced. The helper-produced database and selection entries are exact.
    k=F/("plan_kit_"+name);clone(armed,k,{"k/p.json","BUILD.json","SHA256SUMS.txt"})
    p=J.load(k/"k/p.json");p["n_root"]=str(staged.parent)
    p["uploads"]=[r for r in p["uploads"] if r["sha256"] in (bh,dh,selection["sha256"])]
    p["pin_paths"]={r["sha256"]:p["namespace"]+"/u/"+r["sha256"] for r in p["uploads"]}
    capsule_write(k/"k/p.json",p);seal_new(k)
    sys.path.insert(0,str(k/"b"))
    for module in ("pl","px","z","i"):sys.modules.pop(module,None)
    import pl,z
    index=J.write(F/("index_"+name+".json"),{})
    manifest=J.write(F/("weights_"+name+".json"),dict(index=dict(name="index.json",sha256=index["sha256"]),files=[]))
    handover=J.write(F/("handover_"+name+".json"),dict(pins=dict(full_weights=manifest)))
    small={v["sha256"]:dict(path=v["path"],sha256=v["sha256"],bytes=Path(v["path"]).stat().st_size) for v in (index,manifest)}
    resolved=dict(kit_sha256=J.seal(k),archive=None,small_files=small,receipt=dict(**handover,bytes=Path(handover["path"]).stat().st_size),
        config=dict(streams=dict(routing=dict(path="u/"+bh,sha256=bh)),r1_training=dict(persisted_files={})),
        request=dict(routing_base=dict(path="u/"+bh,sha256=bh)),paths={},tar_sha256="0"*64,tar_bytes=0,parts=[])
    root=F/("node_"+name);root.mkdir()
    request,sources,stage=pl.plan_payload(k,resolved,root,regeneration=False)
    plan=J.load(root/"plan.json");entry=plan["entries"]["u/"+dh]
    assert entry["sha256"]==dh and entry["bytes"]==size and sources[dh]==str(staged/dh)
    assert request["routing_selection"]["sha256"]==selection["sha256"]
    assert dict(path=str(root/"q/u"/dh),sha256=dh) in request["staged_pins"]
    assert not plan["generated"]
    assert J.sha(sources[dh])==dh
    checks.append(dict(kit=name,status="PASS",mode="q",staged_member="u/"+dh,source=sources[dh],bytes=size,full_plan_returned=True))
    # The actual planner must refuse authenticated size/hash mismatches.
    for case in ("size","hash"):
        bad=F/("bad_"+name+"_"+case);bad.mkdir()
        def checked(path,h,n=None):
            if h==dh:return z.checked(path,"0"*64 if case=="hash" else h,size+1 if case=="size" else n)
            return z.checked(path,h,n)
        with patch.object(pl,"checked",checked):
            try:pl.plan_payload(k,resolved,bad,regeneration=False)
            except ValueError as e:assert str(e).startswith("E10:")
            else:raise AssertionError("bad database accepted")
    print(name,"armed decoded scan and native q planner PASS",flush=True)
negative=[]
for case,change,code in (("missing",dict(files=[]),"R1_DATABASE_METADATA_MISSING:"),("size",dict(files=[dict(sha256=dh,size=0)]),"R1_DATABASE_METADATA_SIZE_INVALID"),("conflict",dict(files=[dict(sha256=dh,size=size),dict(sha256=dh,size=size+1)]),"R1_DATABASE_METADATA_SIZE_INVALID")):
    m=F/(case+".json");J.write(m,change)
    with patch.object(arm,"L",fixture_root):
        try:arm.apply(F/"routing_selection.json",m,fixture_root/("bad_"+case),base_path=F/"base.json",**auth)
        except ValueError as e:assert str(e).startswith(code);negative.append(dict(case=case,refusal=str(e)))
        else:raise AssertionError("invalid metadata accepted")
J.write(D/"ARM_TESTS.json",dict(status="PASS",records=checks,negative=negative,upload_excludes_db=True,n_go_not_uploaded=True,all_armed_GO_false=True,
    fixture_manifest=str((fixture_root/"out/armed/UPLOADS_ROUTING_ARMED.json").relative_to(L)),
    scope="Real arming function, decoded scans and complete pl.plan_payload q return on a real SQLite fixture. Compact resolved metadata replaces unrelated production stores/weights; all database/selection/base hashes and sizes are checked by unchanged planner code. No native planner or resolver function is stubbed; negative tests inject hash/size errors only."))
