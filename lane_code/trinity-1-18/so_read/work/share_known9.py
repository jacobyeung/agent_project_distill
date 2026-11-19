"""Share verified immutable fixture bytes, using known references to bound local IO."""
from pathlib import Path
import hashlib,json,os,subprocess,uuid
from datetime import datetime,timezone
L=Path('/scratch/jjyeung/orch_n30/so_read');p=L/'out/checks/STORAGE9.json';old=json.loads(p.read_text())
refs={}
for pin,name in json.loads((L/'work/fixture_pins5.json').read_text()).items():
 f=Path(name)
 if f.is_file() and not f.is_symlink():refs[(f.stat().st_size,pin)]=f
for root in [L/'work/src/u0',*[L/('work/round'+str(i)+'-before-u0') for i in range(3,9)]]:
 for f in root.rglob('*'):
  if f.is_file() and not f.is_symlink():refs[(f.stat().st_size,hashlib.sha256(f.read_bytes()).hexdigest())]=f
anchors={(f.stat().st_dev,f.stat().st_ino) for f in refs.values()}
count=saved=read=0;cut=datetime(2026,11,19,19,10,0,tzinfo=timezone.utc).timestamp()
for d in sorted((L/'work/test-artifacts').iterdir(),key=lambda f:f.stat().st_mtime,reverse=True):
 if not d.is_dir() or d.stat().st_mtime>=cut:continue
 for f in d.rglob('*'):
  if f.is_symlink() or not f.is_file() or f.name=='.wtest':continue
  st=f.stat()
  if st.st_nlink>1 or st.st_size<1024 or (st.st_dev,st.st_ino) in anchors:continue
  if read+st.st_size>100_000_000:continue
  raw=f.read_bytes();read+=len(raw);key=(len(raw),hashlib.sha256(raw).hexdigest());ref=refs.get(key)
  if ref is None:refs[key]=f;anchors.add((st.st_dev,st.st_ino))
  elif ref!=f and ref.read_bytes()==raw:
   tmp=f.with_name(f.name+'.share8'+uuid.uuid4().hex);os.link(ref,tmp);os.replace(tmp,f)
   count+=1;saved+=len(raw)
  if saved>=60_000_000 or read>=99_000_000:break
 if saved>=60_000_000 or read>=99_000_000:break
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0])
result=dict(changed_files=count,unique_bytes_shared=saved,read_bytes=read,workspace_bytes=size)
for key in ('changed_files','unique_bytes_shared','read_bytes'):old[key]+=result[key]
old.update(workspace_bytes=size,passes=old.get('passes',1)+1)
p.write_text(json.dumps(old,sort_keys=True,indent=2)+'\n')
print('Known-reference pass:',json.dumps(result,sort_keys=True));print('Cumulative:',json.dumps(old,sort_keys=True))
