from pathlib import Path
import base64,hashlib,json,shutil,sys,re
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";A=L/"attic/build24e"
sys.path[:0]=[str(L/"work/build24"),str(L/"work/tree_r1")]
import joblib as J
from launch_r2.build import capsule_json

def preserve(p):
 dest=A/p.relative_to(L);dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():return
 p.rename(dest)
 if dest.is_dir():shutil.copytree(dest,p)
 else:shutil.copyfile(dest,p)
def reseal(k):
 fs={str(p.relative_to(k)):J.sha(p) for p in k.rglob("*") if p.is_file() and p.name not in ("SHA256SUMS.txt","BUILD.json")}
 (k/"SHA256SUMS.txt").write_text("".join(f"{h}  {n}\n" for n,h in sorted(fs.items())))
 b=J.load(k/"BUILD.json");b.update(kit_sha256=J.seal(k));(k/"BUILD.json").write_bytes(capsule_json(b));return J.seal(k)
def upgrade(k):
 k=Path(k)
 (k/"b/z.py").write_bytes((L/"work/build24/joblib.py").read_bytes())
 spec=J.load(k/"k/p.json");ns=spec["namespace"]
 closure=J.load(D/"CLOSURE.json");uploads={x["sha256"]:x for x in spec["uploads"]}
 for h,v in closure["added"].items():uploads[h]={key:v[key] for key in ("opaque_name","bytes","sha256")}
 spec["uploads"]=[uploads[h] for h in sorted(uploads)];spec["pin_paths"]={h:ns+"/u/"+h for h in uploads}
 replacements={h:"u/"+h for h in uploads};replacements.update({h:"u/"+h for h in closure["host_pins"]})
 spec["host_paths"]=closure["host_pins"]
 def relocate(v):
  if isinstance(v,dict):
   if "path" in v and "sha256" in v and v["sha256"] in replacements:return dict(v,path=replacements[v["sha256"]])
   return {key:(x if key in ('p_run','init_artifact') else relocate(x)) for key,x in v.items()}
  if isinstance(v,list):return [relocate(x) for x in v]
  return v
 for filename in ("n.json","c.json","r.json","h.json"):
  p=k/"k"/filename
  if p.exists():(p).write_bytes(capsule_json(relocate(J.load(p))))
 # p_pins is provenance for the sealed donor map, retained as authenticated bytes.
 spec["p_pins"]=relocate(spec["p_pins"])
 (k/"k/p.json").write_bytes(capsule_json(spec))
 p=k/"b/f.sh";s=p.read_text();marker="N=\"${1:?}.h\""
 check="""case "${1:-}" in /*) ;; *) echo E06 >&2; exit 1 ;; esac
P="$(readlink -m -- "$1")"
case "$P" in /tmp/*) ;; *) echo E06 >&2; exit 1 ;; esac
N="$P.h"
"""
 if marker in s:s=s.replace(marker,check).replace("p \"$1\"","p \"$P\"")
 p.write_text(s)
 p=k/"job.sh";s=p.read_text()
 if "R=\"$(readlink" not in s:
  s=s.replace("umask 077\n","umask 077\nR=\"$(readlink -f -- \"${1:?E87}\")\" || { echo E87 >&2; exit 1; }\n[[ -f \"$R\" ]] || { echo E87 >&2; exit 1; }\n")
  s=s.replace("\"${1:?}\" \"$N\"","\"$R\" \"$N\"")
 p.write_text(s)
 p=k/'b/u.py'
 if p.exists():
  source=p.read_text()
  source=source.replace("with scope(cfg['r1_training']['persisted_files']):", "request=load(r.parent/'r.json')\nfrom launch_r1.production_proof import verify_staging\nwith scope(request['_paths']),scope(cfg['r1_training']['persisted_files']):\n verify_staging(request)")
  p.write_text(source)
 return reseal(k)
def main():
 rows=J.load(D/"PATHS_BEFORE.json");uploads={v["sha256"]:v for v in J.load(L/"work/build24d/UPLOADS_q.json")["files"] if v["opaque_name"].startswith("u/")}
 added={};host={};missing={}
 for h,r in {r["sha256"]:r for r in rows if r["kind"]=="pin" and r["path"].startswith("/scratch/jjyeung")}.items():
  if h in uploads:continue
  p=Path(r["path"])
  if p.suffix in (".sqlite",".db"):
   receipt=J.load(uploads["e3ee51daa46af30fa8e84a05c12448d7fc3dc9cade05284707f9df322bbe44d0"]["local_path"])
   assert receipt["database"]["sha256"]==h
   host[h]=receipt["database"]["path"];continue
  assert p.stat().st_size<20_000_000 and J.sha(p)==h
  target=D/"pins"/h;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
  added[h]=dict(local_path=str(target),opaque_name="u/"+h,bytes=target.stat().st_size,sha256=h)
 J.write(D/"CLOSURE.json",dict(added=added,host_pins=host))
 for p in (L/"work/build24/kits/q",L/"work/build24/kits/n",L/"out/kit_n_go"):preserve(p);print(p.name,upgrade(p))
 p=L/"work/build24c/runtime.py";preserve(p);s=p.read_text()
 s+="\n    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/\"work/build24e\"))\n    from patch24e import upgrade as upgrade24e\n    upgrade24e(k)\n"
 p.write_text(s)
 # A unique import name avoids the historical patch modules.
 (D/"patch24e.py").write_text(Path(__file__).read_text())
 print("added",[(h,v["bytes"]) for h,v in added.items()],"host",host)
if __name__=="__main__":main()
