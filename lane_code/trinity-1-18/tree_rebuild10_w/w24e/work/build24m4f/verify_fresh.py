from common import *
import tarfile,subprocess,io,importlib.util,contextlib
from unittest.mock import patch
v=J.load(L/"out/DELIVERY_24M4F.json");archive=L/v["package"];root=L/"work/build24m4f_fresh"
assert not root.exists()
assert J.sha(archive)==v["sha256"]
check=J.load(D/"PACKAGE_CHECK.json")
assert v["storage"]["conservative_upper_bound_bytes"]+check["unique_uncompressed_bytes"]+10_000_000<100_000_000
root.mkdir();members={}
with tarfile.open(archive,mode="r|*") as t:
 for m in t:
  p=root/m.name
  assert not Path(m.name).is_absolute() and ".." not in Path(m.name).parts
  p.parent.mkdir(parents=True,exist_ok=True)
  if m.islnk():
   assert m.linkname in members
   source=root/m.linkname;assert source.stat().st_mode&511==m.mode
   os.link(source,p);h=members[m.linkname]["sha256"];size=source.stat().st_size
  else:
   assert m.isfile();h0=hashlib.sha256();size=0
   with p.open("xb") as f:
    for b in iter(lambda:t.extractfile(m).read(),b""): # One bounded member read.
     f.write(b);h0.update(b);size+=len(b);break
   p.chmod(m.mode);h=h0.hexdigest();assert size==m.size
  members[m.name]=dict(sha256=h,bytes=size,mode=format(m.mode,"04o"))
manifest=json.loads((root/"work/build24m4f/PACKAGE_MANIFEST.json").read_text())
assert all(members[n]==r for n,r in manifest["files"].items())
assert hashlib.sha256(json.dumps(manifest["files"],sort_keys=True,separators=(",",":")).encode()).hexdigest()==v["package_seal"]
assert len(members)==v["verified_members"]
assert not set(J.load(D/"MEMBERS_24M4C.json"))-set(members)
r=subprocess.run([sys.executable,"-s","-B",str(root/"out/arm_routing.py"),"--help"],capture_output=True,text=True,cwd=root)
assert r.returncode==0,r.stderr
for flag in ("--reviewed-selection-sha256","--reviewed-regenerated-sha256","--review-verdict"):assert flag in r.stdout
# Load only package-local arming dependencies for a fresh-package real CLI run.
for name in ("support","joblib","environment21f"):
 sys.modules.pop(name,None)
sp=importlib.util.spec_from_file_location("fresh_arm",root/"out/arm_routing.py");arm=importlib.util.module_from_spec(sp);sp.loader.exec_module(arm)
assert Path(sys.modules["support"].__file__).is_relative_to(root)
assert Path(arm.J.__file__).is_relative_to(root)
F=root/"work/build24m4f/arming_final";workspace=F/"workspace"
args=[str(root/"out/arm_routing.py"),str(F/"routing_selection.json"),str(F/"db_bytes.json"),"--reviewed-selection-sha256",J.sha(F/"routing_selection.json"),"--reviewed-regenerated-sha256",J.load(F/"routing_selection.json")["regenerated_sha256"],"--review-verdict",str(F/"REVIEW_RESULT.txt"),"--routing-base",str(F/"base.json"),"--output",str(workspace/"out/fresh_cli_armed")]
with patch.object(arm,"L",workspace),patch.object(sys,"argv",args):
 output=io.StringIO()
 with contextlib.redirect_stdout(output):arm.main()
 printed=json.loads(output.getvalue())
result=J.load(workspace/"out/fresh_cli_armed/UPLOADS_ROUTING_ARMED.json")
assert printed["kits"]==result["kits"] and printed["armed_n_go_config"]==result["armed_n_go_config"]
for name,expected in v["kits"].items():
 k=root/("out/kit_n_go" if name=="n_go" else "out/kit_qd" if name=="qd" else "work/build24/kits/"+name)
 assert arm.J.seal(k)==expected
known=J.load(D/"DISK_BASELINE.json");seen=set();growth=0
for parent,dirs,names in os.walk(L):
 dirs[:]=[n for n in dirs if n!=".git" and not Path(parent,n).is_symlink()]
 for n in dirs+names:
  s=Path(parent,n).lstat();key=f"{s.st_dev}:{s.st_ino}"
  if key not in seen:growth+=max(0,s.st_blocks-known.get(key,0))*512;seen.add(key)
assert growth+1_000_000<100_000_000,growth
record=dict(status="PASS",archive_sha256=v["sha256"],members=len(members),all_member_bytes_and_modes_verified=True,all_24m4c_members_present=True,package_manifest_seal_verified=True,package_local_helper_import=True,real_cli_success=True,printed=printed,kit_seals=v["kits"],new_allocated_bytes=growth)
J.write(D/"FRESH_PACKAGE_CHECK.json",record)
v["fresh_package_check"]="work/build24m4f/FRESH_PACKAGE_CHECK.json"
v["storage"]=dict(new_allocated_bytes=growth,conservative_upper_bound_bytes=growth+1_000_000,cap_bytes=100_000_000,cap_met=True,transient_cap_met=True,includes_fresh_unpack=True)
J.write(L/"out/DELIVERY_24M4F.json",v)
J.write(D/"STORAGE_FINAL.json",v["storage"])
print(json.dumps(dict(status="PASS",members=len(members),real_cli_success=True,storage=v["storage"]),indent=2),flush=True)
