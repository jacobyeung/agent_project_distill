from pathlib import Path
import sys,json,hashlib,tarfile,stat,resource
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
J=Path.cwd();D=J/'work/build24m4z3';P=J.parent/'w24y2/out/tree_rebuild_b24m4y2_42b4d736.tar'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
roots=['out/kit_n_go','work/build24/kits/n','work/build24/kits/q','out/kit_qd','out/rcj','work/tree_r1c','work/tree_r1']
old={r:{} for r in roots};seen={};count=0
package_sha=sha(P);assert package_sha.startswith('15cdc127'),package_sha
print('Archive sha256',package_sha,flush=True)
with tarfile.open(P,'r|*') as t:
 for m in t:
  count+=1
  if m.isfile():
   h=hashlib.sha256()
   with t.extractfile(m) as f:
    for b in iter(lambda:f.read(1<<20),b''):h.update(b)
   value=dict(sha256=h.hexdigest(),bytes=m.size,mode=m.mode,type='file')
  elif m.islnk():value=dict(seen[m.linkname],mode=m.mode)
  elif m.issym():value=dict(type='symlink',target=m.linkname,mode=m.mode)
  elif m.isdir():continue
  else:raise AssertionError(m.name)
  seen[m.name]=value
  for r in roots:
   if m.name.startswith(r+'/'):old[r][m.name[len(r)+1:]]=value
print('Streamed archive members',count,flush=True)
def inventory(root):
 return {str(p.relative_to(root)):dict(sha256=sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511,type='file') for p in root.rglob('*') if p.is_file()}
allowed={'b/o.py','b/pc.py','b/pc.sh','k/y.json','SHA256SUMS.txt','BUILD.json'}
rows={}
for r in roots:
 current=inventory(J/r);baseline=old[r]
 added=sorted(set(current)-set(baseline));missing=sorted(set(baseline)-set(current))
 changed=sorted(n for n in current.keys()&baseline.keys() if current[n]!=baseline[n])
 rows[r]=dict(files=len(current),added=added,missing=missing,changed=changed)
 assert not added and not missing,(r,added,missing)
 assert set(changed)==(allowed if r in ('out/kit_n_go','work/build24/kits/n') else set()),(r,changed)
n=inventory(J/'out/kit_n');go=inventory(J/'out/kit_n_go');assert n==inventory(J/'work/build24/kits/n')
diff=sorted(p for p in n if n[p]!=go[p]);assert diff==['BUILD.json','SHA256SUMS.txt','k/a.json'],diff
rows['out/kit_n']=dict(files=len(n),added=[],missing=[],changed=sorted(p for p in n if n[p]!=old['work/build24/kits/n'][p]),baseline='work/build24/kits/n')
sys.path.insert(0,str(J/'work/tree_r1c'))
from student_pilot.source_seal import inventory as tree_inventory
from student_pilot.p3_provenance import digest
tree=digest(tree_inventory(J/'work/tree_r1c'));assert tree=='9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b'
result=dict(status='PASS',source_archive_sha256=package_sha,archive_members=count,full_diff=rows,n_go_difference=diff,tree_sha256=tree,scope='Every regular-file byte, size, mode and membership in named roots, streamed from the supplied final archive')
(D/'DELTA.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
(D/'BASELINE_FILES.json').write_text(json.dumps(old,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2),flush=True)
