from common import *
from student_pilot.source_seal import inventory,check_archive
from student_pilot.p3_provenance import digest,file_pin
from launch_r1.build import verify
from copy import deepcopy

original=J.load(D/"ORIGINAL_KITS.json");preserved={};content=[];modes=[]
for rel,item in original.items():
    p=L/rel;current=dict(sha256=J.sha(p),mode=p.stat().st_mode&511,bytes=p.stat().st_size)
    if current!=item:
        old=L/"attic/build24m4d"/rel
        assert old.is_file() and J.sha(old)==item["sha256"] and old.stat().st_mode&511==item["mode"],rel
        preserved[rel]=str(old.relative_to(L))
    else:preserved[rel]=rel
    if current["sha256"]!=item["sha256"]:content.append(rel)
    if current["mode"]!=item["mode"]:modes.append(rel)
allowed={str((kit(n)/rel).relative_to(L)) for n in ("q","n","n_go","qd") for rel in ("b/rv.py","BUILD.json","SHA256SUMS.txt")}
assert set(content)==allowed,content
files=inventory(T);tree=digest(files);assert files==J.load(L/"work/build24m4c/TREE24L4_SEAL.json")["files"]
assert tree=="0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de"
seals={}
for name in ("q","n","n_go","qd"):
    k=kit(name);seals[name]=verify(k)
    assert J.load(k/"k/a.json")["GO"]==(name=="n_go")==J.load(k/"BUILD.json")["GO"]
    assert J.load(k/"k/7.json")["files"]==files==J.load(k/"k/c0.json")["files"]
    check_archive(file_pin(k/J.load(k/"k/a.json")["source"]["path"]),files)
    assert J.load(D/("SCAN_"+name+".json"))["kit_seal"]==seals[name]
    for p in k.rglob("*"):
        if p.is_file():
            before=original[str(p.relative_to(L))]["mode"];after=p.stat().st_mode&511
            assert after==(before if before&0o111 else 0o644),(p,before,after)
J.write(D/"INVARIANTS.json",dict(status="PASS",tree_sha256=tree,tree_files=len(files),kits=seals,
    content_changed=content,mode_changes=len(modes),preserved_originals=preserved,
    unchanged=["All tree bytes and kit tree archives","All training configs and census semantics","Admission, legality, removals, opener rows, step-544 lineage, resolver identity checks and DEFERRED boundary","b/pc.py stop checkpoint order"],GO="false except unuploaded out/kit_n_go"))
# Orchard is the supplied 24m2d inventory with UPLOADS_24M3 applied.
base=deepcopy(J.load(L/"work/build24m3/BASELINE.json"));m3=J.load(L/"out/UPLOADS_24M3.json")
known={}
for r in m3["files"]:
    name=r["name"];known[name]=r
    top,rel=name.split("/",1)
    if top in base:base[top][rel]=dict(sha256=r["sha256"],bytes=r["bytes"],mode=int(r["mode"],8))
J.write(D/"ORCHARD_24M3_BASELINE.json",dict(basis="24m2d plus out/UPLOADS_24M3.json",manifest_sha256=J.sha(L/"out/UPLOADS_24M3.json"),kits=base))
upload=D/"upload";upload.mkdir();records=[]
def record(p,name,action):return dict(name=name,sha256=J.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,"04o"),local_path=str(p),action=action)
for name in ("q","n","qd"):
    for p in sorted(kit(name).rglob("*")):
        if not p.is_file():continue
        rel=str(p.relative_to(kit(name)));old=base[name].get(rel)
        if old and J.sha(p)==old["sha256"] and p.stat().st_mode&511==old["mode"]:continue
        dst=upload/name/rel;dst.parent.mkdir(parents=True,exist_ok=True);os.link(p,dst)
        records.append(record(dst,name+"/"+rel,"replace" if old else "add"))
for p in sorted((L/"work/build24m4c/u").iterdir()):
    name="u/"+p.name
    if name in known and J.sha(p)==known[name]["sha256"]:continue
    dst=upload/name;dst.parent.mkdir(parents=True,exist_ok=True);os.link(p,dst);records.append(record(dst,name,"add"))
# The discovery wrapper and dbb2 bytes already match the applied 24m3 delta.
for r in m3["outside_kit_files"]:assert J.sha(L/"out"/r["name"])==r["sha256"]
up=dict(schema="build24m4d-upload-diff-v1",baseline="24m3: out/UPLOADS_24M3.json applied on top of 24m2d",baseline_manifest_sha256=J.sha(L/"out/UPLOADS_24M3.json"),
    baseline_inventory="work/build24m4d/ORCHARD_24M3_BASELINE.json",baseline_inventory_sha256=J.sha(D/"ORCHARD_24M3_BASELINE.json"),
    stream_root=str(upload),top_directories=["q","n","qd","u"],files=records,total_files=len(records),total_bytes=sum(r["bytes"] for r in records),
    kits={n:seals[n] for n in ("q","n","qd")},GO=False,n_go_upload_authorized=False,outside_kit_files=[],uploaded=False)
J.write(L/"out/UPLOADS_24M4D.json",up);(L/"out/UPLOADS_24M4D.list").write_text("".join(r["name"]+"\n" for r in records))
go=[]
for p in sorted(kit("n_go").rglob("*")):
    if p.is_file():
        rel=p.relative_to(kit("n_go"))
        if J.sha(p)!=J.sha(kit("n")/rel):go.append(record(p,"n/"+str(rel),"replace"))
assert {r["name"] for r in go}=={"n/k/a.json","n/BUILD.json","n/SHA256SUMS.txt"}
J.write(L/"out/UPLOADS_24M4D_GO.json",dict(schema="build24m4d-go-diff-v1",base_kit_seal=seals["n"],kit_seal=seals["n_go"],files=go,total_files=len(go),total_bytes=sum(r["bytes"] for r in go),upload_authorized=False))
print("Tree, originals, scope and modes PASS; upload delta",len(records),up["total_bytes"],flush=True)
