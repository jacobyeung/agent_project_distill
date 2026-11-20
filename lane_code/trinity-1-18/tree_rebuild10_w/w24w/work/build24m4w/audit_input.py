from pathlib import Path
import sys,json,os,stat
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4w';sys.path.insert(0,str(D))
from seal import z,write,replace
base=z.load(L/'work/build24m4t/PACKAGE_MANIFEST.json')['files']
allowed={'work/tree_r1c/student_pilot/'+n for n in ('extent_receipt.py','carrier_c1_run.py','r1_routing.py','r2_intake.py')}|{'out/rcj/ch.py','out/TREE_SEAL.json','out/TREE_FILES.sha256'}
for n in ('q','n','n_go','qd'):
 prefix='out/kit_'+n if n in ('n_go','qd') else 'work/build24/kits/'+n
 allowed|={prefix+'/'+rel for rel in ('BUILD.json','SHA256SUMS.txt','k/7.json','k/a.json','k/c.json','k/c0.json','k/n.json','k/p.json','k/t_e047002134f979bd.tar')}
cache={};changed=[];restored=[]
for rel,v in base.items():
 p=L/rel;st=p.lstat()
 if v['type']=='symlink':assert p.is_symlink() and os.readlink(p)==v['target'],rel;continue
 key=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
 if key not in cache:cache[key]=z.sha(p)
 now=dict(type='file',sha256=cache[key],bytes=st.st_size,mode=st.st_mode&511)
 if now==v:continue
 if rel not in allowed:
  source=L.parent/'w24t'/rel
  assert source.is_file() and z.sha(source)==v['sha256'],(rel,v,now)
  replace(p,source.read_bytes());p.chmod(v['mode']);restored.append(dict(path=rel,expected_sha256=v['sha256'],before=now))
 else:
  saved=L/'attic/build24m4w'/rel
  assert saved.is_file() and z.sha(saved)==v['sha256'],rel
  changed.append(rel)
assert set(changed)==allowed,(sorted(set(changed)-allowed),sorted(allowed-set(changed)))
write(D/'INPUT_AUDIT.json',dict(status='PASS',members=len(base),intended_changes=sorted(changed),restored_fixture_aliases=restored,source='24m4t package manifest',no_input_members_removed=True))
print(json.dumps(dict(status='PASS',members=len(base),changed=len(changed),restored_fixture_aliases=len(restored)),indent=2))
