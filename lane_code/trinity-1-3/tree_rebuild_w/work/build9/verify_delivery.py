"""Authenticate final artifacts and measure the lane without following links."""
import hashlib,json,os,shutil,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9'
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest,load
from launch_r2.build import verify,scan
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
seal=json.loads((L/'out/TREE_SEAL.json').read_text())
delivery=json.loads((B/'DELIVERY.json').read_text())
files=inventory(L/'work/tree_r1')
assert files==seal['files'] and digest(files)==seal['tree_sha256']==delivery['tree_seal']
assert sha(L/'out/TREE_FILES.sha256')==seal['inventory_sha256']
assert sha(L/'out/TREE.diff')==seal['diff_sha256']
assert sha(L/delivery['path'])==delivery['sha256']
assert (L/delivery['path']).stat().st_size==delivery['bytes']<150_000_000
kits={}
for arm in ('a2','a0'):
 p=B/'kits'/arm;kits[arm]=dict(sha256=verify(p),scan=scan(p))
 launch=load(p/'k/launch.json')
 assert launch['source_revision']=='sha256:'+seal['tree_sha256']
 assert not launch['production_authorized']
sizes=dict(lane=0,tmp=0);pending=[str(L)];files_count=0
while pending:
 with os.scandir(pending.pop()) as entries:
  for entry in entries:
   if entry.is_symlink():continue
   if entry.is_dir(follow_symlinks=False):pending.append(entry.path)
   elif entry.is_file(follow_symlinks=False):
    count=entry.stat(follow_symlinks=False).st_size;sizes['lane']+=count;files_count+=1
    if entry.path.startswith(str(L/'work/tmp')+'/'):sizes['tmp']+=count
assert sizes['lane']<=7_000_000_000 and sizes['tmp']<=200_000_000
result=dict(tree_seal=seal['tree_sha256'],tree_files=len(files),delivery=delivery,kits=kits,
 storage_bytes=sizes,scratch_free_bytes=shutil.disk_usage('/scratch').free,files_measured=files_count,
 limitations='Hash and storage verification do not close the named launch or acceptance blockers.')
(B/'FINAL_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
