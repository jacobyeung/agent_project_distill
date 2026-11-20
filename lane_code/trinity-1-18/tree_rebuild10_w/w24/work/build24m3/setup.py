from common import *
import gzip,subprocess,tarfile
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
X=L.parent/"work/x24l4r_back/out"
seen={}
for root,dirs,files in os.walk(L):
 dirs[:]=[n for n in dirs if not Path(root,n).is_symlink()]
 for name in dirs+files:
  s=Path(root,name).lstat();seen[str(s.st_dev)+":"+str(s.st_ino)]=s.st_blocks
(D/"DISK_BASELINE.json.gz").write_bytes(gzip.compress(json.dumps(seen).encode(),mtime=0))
base={n:{str(p.relative_to(kit(n))):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in kit(n).rglob("*") if p.is_file()} for n in ("q","n","n_go","qd")}
J.write(D/"BASELINE.json",base)
J.write(D/"PRIOR_PACKAGES.json",{str(p):J.sha(p) for p in (L/"out").glob("tree_rebuild*.tar")})
before=inventory(T);spec=J.load(X/"UNCHANGED24L4R.json");expected=J.load(X/"TREE24L4R_SEAL.json")
assert digest(before)==spec['before_tree_sha256']
for n,v in spec['files'].items():assert before.get(n)==v['before'],n
patch=X/'HOST24L4R.patch'
r=subprocess.run(['patch','--dry-run','--fuzz=0','--batch','-p1','-i',str(patch)],cwd=T,capture_output=True,text=True)
(D/'patch_dry.log').write_text(r.stdout+r.stderr);assert r.returncode==0
for n in spec['changed']:
 p=T/n
 if p.exists():replace(p,p.read_bytes(),p.stat().st_mode&511)
r=subprocess.run(['patch','--fuzz=0','--batch','-p1','-i',str(patch)],cwd=T,capture_output=True,text=True)
(D/'patch.log').write_text(r.stdout+r.stderr);assert r.returncode==0
actual=inventory(T);assert actual==expected['files'];assert digest(actual)==spec['after_tree_sha256']
for n,v in spec['files'].items():assert actual.get(n)==v['after'],n
package=X/'tree_rebuild_b24l4r_92fe11f8.tar'
assert J.sha(package)=='db64b3266674f0669759badbbbd3d8791f51a981f40872e412c6a2cbfdc21748'
with tarfile.open(package) as f:
 inside={m.name[len('work/tree_r1/'):]:hashlib.sha256(f.extractfile(m).read()).hexdigest() for m in f if m.isfile() and m.name.startswith('work/tree_r1/')}
assert inside==actual
J.write(D/'TREE_VERIFICATION.json',dict(status='PASS',tree_sha256=digest(actual),files=len(actual),fuzz=0,archive_matches=True))
for name in ('TREE24L4R_SEAL.json','UNCHANGED24L4R.json','HOST24L4R.patch','PROTECTED_ROOMS_API.md'):(D/name).write_bytes((X/name).read_bytes())
print('Tree verified',digest(actual),len(actual))
