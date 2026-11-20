from pathlib import Path
import sys,runpy,json,shutil,hashlib,tarfile,io,difflib
L=Path.cwd();D=L/"work/build24m4y";V=L.parent/"w24v"
sys.path[:0]=[str(L/"work/tree_r1c"),str(L/"out/kit_qd/b")]
import z
from launch_r1.build import verify
from student_pilot.source_seal import inventory,check_archive
from student_pilot.p3_provenance import digest,file_pin
A=runpy.run_path(str(V/"out/apply_24m4v.py"))["DATA"]
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+"\n")
def files(k):return {str(p.relative_to(k)):dict(sha256=z.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in k.rglob("*") if p.is_file()}
base=json.loads((L/"work/build24m4s/BASELINE.json").read_text())
assert {n:base["kits"][n][:8] for n in ("q","n","qd")}==dict(q="e7ac0727",n="a7809da0",qd="221d1782")
assert {n:h[:8] for n,h in base["rcj"].items()}=={"x.py":"d8517333","ch.py":"16d7210b","nd.py":"eb0ba92e","f.json":"37cbc05d","pc.py":"bd87252b","ps.py":"6945292e","rcj.sh":"b23393f2","P_SAMPLE_I.json":"fff742bb"}
T=L/"work/tree_r1c";inv=inventory(T);tree=digest(inv);assert tree==A["tree"]
old=json.loads((V/"work/build24m4v/BASELINE.json").read_text())["inventory"]
changed=sorted(n for n in inv if old[n]!=inv[n]);assert set(old)==set(inv)
assert changed==sorted(n.removeprefix("work/tree_r1c/") for n in A["files"] if n.startswith("work/tree_r1c/"))
for n in inv:assert z.sha(T/n)==z.sha(V/"work/tree_r1c"/n)
assert inv["student_pilot/s1_scene_census.py"]==old["student_pilot/s1_scene_census.py"]
pref=json.loads((D/"PREFLIGHT.json").read_text())
for n,h in pref["helpers_before"].items():
 if n!="ch.py":assert z.sha(L/"out/rcj"/n)==h,n
assert z.sha(L/"out/rcj/ch.py")==z.sha(V/"out/rcj/ch.py")
seals={};current={};merges=[]
for name,rel in A["kit_paths"].items():
 k=L/rel;seals[name]=verify(k);assert seals[name]==A["kits"][name]
 current[name]=files(k)
 for n in ("k/a.json","BUILD.json"):assert z.load(k/n)["GO"]==(name=="n_go")
 check_archive(file_pin(k/z.load(k/"k/a.json")["source"]["path"]),inv)
 for n in ("k/c.json","k/n.json"):
  value=z.load(k/n);before=z.load(L/"attic/build24m4v_apply"/rel/n)
  assert value["r1_training"].pop("extent_pool_sources")==A["sources"]
  assert value["extent_receipt"]==before["extent_receipt"] and value["extent_receipt"]["sha256"]==A["receipt"]
  value["code"]=before["code"];assert value==before
 for n in ("k/7.json","k/c0.json"):
  value=z.load(k/n);assert value["files"]==inv and value["tree_sha256"]==tree
 for n in current[name]:
  saved=L/"attic/build24m4v_apply"/rel/n
  if saved.exists():merges.append(dict(file=str(Path(rel)/n),method="Applied authenticated route-T config/source update to 24m4u base; regenerated seals; other kit bytes retained",before=z.sha(saved),after=z.sha(k/n)))
write(D/"MERGE.json",dict(status="PASS",conflicting_helper_edits=[],manual_code_merges_required=False,helpers={"ch.py":"24m4v exact bytes: chain controls, counters, card and route-T pin","x.py":"24m4u exact bytes: bounded publication, staged child runtime and diagnostics","nd.py":"24m4u exact bytes: sample and refusal diagnostics","ps.py":"Identical in both inputs; retained","pc.py":"Identical in both inputs; retained","f.json":"Identical in both inputs; retained","rcj.sh":"Identical in both inputs; retained","P_SAMPLE_I.json":"Identical in both inputs; retained"},kit_files=merges))
write(D/"SEALS_FINAL.json",dict(tree=tree,kits=seals,receipt=A["receipt"],changed_tree_files=changed,census_compare_unchanged=True))
rows=[];optional=[]
def entry(name,p,old=None):return dict(name=name,relative_path=str(p.relative_to(L)),local_path=str(p),action="replace" if old else "add",baseline_sha256=old,sha256=z.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,"04o"))
for n,rel in A["kit_paths"].items():
 assert current[n].keys()==base["files"][n].keys()
 for f,v in current[n].items():
  if v!=base["files"][n][f]:(optional if n=="n_go" else rows).append(entry(n+"/"+f,L/rel/f,base["files"][n][f]["sha256"]))
for n,h in base["rcj"].items():
 p=L/"out/rcj"/n
 if z.sha(p)!=h:rows.append(entry("rcj/"+n,p,h))
for p in (L/"work/build24m4v_apply/u").iterdir():rows.append(entry("u/"+p.name,p))
rows.sort(key=lambda v:v["name"]);optional.sort(key=lambda v:v["name"])
assert [v["name"] for v in rows if v["name"].startswith("rcj/")]==["rcj/ch.py","rcj/nd.py","rcj/x.py"]
for suffix,items in (("",rows),("_GO",optional)):
 up=dict(schema="cpu-publication-delta-v1",build="24m4w",baseline="Reviewed Orchard overlay",baseline_kit_seals={n:base["kits"][n] for n in (("n_go",) if suffix else ("q","n","qd"))},baseline_rcj=base["rcj"],tree_sha256=tree,kit_seals={n:seals[n] for n in (("n_go",) if suffix else ("q","n","qd"))},files=items,total_files=len(items),total_bytes=sum(v["bytes"] for v in items),GO=bool(suffix),uploaded=False,launched=False,over_5MB=[dict(name=v["name"],bytes=v["bytes"]) for v in items if v["bytes"]>5000000])
 write(L/"out"/("UPLOADS_24M4W"+suffix+".json"),up)
 (L/"out"/("UPLOADS_24M4W"+suffix+".list")).write_text("".join(v["name"]+"\n" for v in items))
replay=D/"upload_replay";replay.mkdir()
def copy(p,q,mode):q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);q.chmod(mode)
for n,rel in A["kit_paths"].items():
 for f,v in base["files"][n].items():
  p=L/rel/f
  candidates=[p]+[L/"attic"/b/rel/f for b in ("build24m4v_apply","build24m4t","build24m4s")]+[L/"work/build24m4u/reviewed_before"/n/f]
  source=next((p for p in candidates if p.is_file() and z.sha(p)==v["sha256"]),None);assert source,(n,f)
  copy(source,replay/n/f,v["mode"])
 assert verify(replay/n)==base["kits"][n]
for n,h in base["rcj"].items():
 candidates=[L/"out/rcj"/n]+[L/"attic"/b/"out/rcj"/n for b in ("build24m4v_apply","build24m4u","build24m4t")]+[L/"work/build24m4u/reviewed_before/rcj"/n]
 p=next(p for p in candidates if p.is_file() and z.sha(p)==h);copy(p,replay/"rcj"/n,p.stat().st_mode&511)
for v in rows+optional:
 q=replay/v["name"]
 if q.exists():
  saved=L/"attic/build24m4y/upload_replay"/v["name"];saved.parent.mkdir(parents=True,exist_ok=True);q.rename(saved)
 copy(L/v["relative_path"],q,int(v["mode"],8))
for n in A["kit_paths"]:assert verify(replay/n)==seals[n] and files(replay/n)==current[n]
assert files(replay/"rcj")==files(L/"out/rcj")
for v in rows+optional:assert z.sha(replay/v["name"])==v["sha256"]
write(D/"DELTA_REPLAY.json",dict(status="PASS",ordinary_files=len(rows),optional_files=len(optional),bytes=sum(v["bytes"] for v in rows),exact_bytes_modes=True,kits=seals))
sha_list="".join(inv[n]+"  "+n+"\n" for n in changed).encode();(L/"out/TREE_PATCH_24M4W.sha256").write_bytes(sha_list)
patch=L/"out/TREE_PATCH_24M4W.tar"
with tarfile.open(patch,"w") as tar:
 for n in changed:
  raw=(T/n).read_bytes();m=tarfile.TarInfo(n);m.size=len(raw);m.mode=(T/n).stat().st_mode&511;tar.addfile(m,io.BytesIO(raw))
 m=tarfile.TarInfo("SHA256SUMS.txt");m.size=len(sha_list);m.mode=0o644;tar.addfile(m,io.BytesIO(sha_list))
with tarfile.open(patch) as tar:
 assert set(tar.getnames())==set(changed)|{"SHA256SUMS.txt"}
 for n in changed:assert hashlib.sha256(tar.extractfile(n).read()).hexdigest()==inv[n]
 assert tar.extractfile("SHA256SUMS.txt").read()==sha_list
write(D/"TREE_PATCH_CHECK.json",dict(status="PASS",bytes=patch.stat().st_size,sha256=z.sha(patch),changed_tree_files=changed,metadata="SHA256SUMS.txt"))
print(json.dumps(dict(status="PASS",uploads=len(rows),upload_bytes=sum(v["bytes"] for v in rows),optional=len(optional),patch_bytes=patch.stat().st_size,kits=seals),indent=2))
