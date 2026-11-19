from pathlib import Path
import ast,json,shutil,sys,difflib
L=Path(__file__).resolve().parents[2];D=L/'work/build24c';A=L/'attic/build24c'
sys.path[:0]=[str(D),str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from runtime import harden_kit
from launch_r2.build import capsule_json

def save(p):
 a=A/p.relative_to(L);a.parent.mkdir(parents=True,exist_ok=True)
 assert not a.exists();p.rename(a);shutil.copyfile(a,p)

def reseal(k):
 fs={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
 (k/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(fs.items())))
 b=J.load(k/'BUILD.json');b.update(GO=False,kit_sha256=J.seal(k));(k/'BUILD.json').write_bytes(capsule_json(b))
 return J.seal(k)

def main():
 records={};changes={}
 for name in ('q','n'):
  k=L/'work/build24/kits'/name;a=A/('kit_'+name)
  assert not a.exists();k.rename(a);shutil.copytree(a,k)
  before={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file()}
  harden_kit(k);seal=reseal(k)
  changes[name]=[str(p.relative_to(k)) for p in k.rglob('*') if p.is_file() and J.sha(p)!=before.get(str(p.relative_to(k)))]
  records[name]={**J.load(L/'work/build24b/KIT.json')[name],'kit_seal':seal}
  uploads=[x for x in J.load(L/'work/build24b'/('UPLOADS_'+name+'.json'))['files'] if x['opaque_name'].startswith('u/')]
  uploads += [dict(local_path=str(p),opaque_name=name+'/'+str(p.relative_to(k)),sha256=J.sha(p),bytes=p.stat().st_size,needed_minimal=True) for p in k.rglob('*') if p.is_file()]
  J.write(D/('UPLOADS_'+name+'.json'),dict(files=uploads,total_bytes=sum(x['bytes'] for x in uploads)))
 # All inherited kit generators postprocess the complete emitted kit before
 # sealing it. The immutable sealed-tree generator is covered by this wrapper.
 generators=['work/build20/kit.py','work/build21/base/kit.py','work/build21/kit.py','work/build22/kit.py','work/build24b/kit.py']
 diffs=[]
 for name in generators:
  p=L/name;s=p.read_text();old=s;save(p)
  if name=='work/build24b/kit.py':
   marker="  cap(k,'BUILD.json',build);seal=reseal(k)"
   replacement="  sys.path.insert(0,str(L/'work/build24c'))\n  from runtime import harden_kit\n  harden_kit(k)\n"+marker
  else:
   marker="manifest={str(p.relative_to(K))"
   replacement="sys.path.insert(0,str(L/'work/build24c'))\nfrom runtime import harden_kit\nharden_kit(K)\n"+marker
  assert marker in s,name;s=s.replace(marker,replacement)
  p.write_text(s);ast.parse(s)
  diffs.extend(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=name+' before',tofile=name))
 p=L/'work/build24/joblib.py';s=p.read_text();save(p)
 s=s.replace("'Q_ROOT':env_node", "'PYTHONDONTWRITEBYTECODE':'1','Q_ROOT':env_node");p.write_text(s)
 J.write(D/'KIT.json',records);J.write(D/'CHANGES.json',dict(kits=changes,generators=generators,tree_changed=False))
 (D/'GENERATORS.diff').write_text(''.join(diffs))
 print(json.dumps(records,indent=2))
if __name__=='__main__':main()
