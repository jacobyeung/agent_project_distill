from pathlib import Path
import ast,hashlib,json,shutil,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24d'
sys.path[:0]=[str(D),str(L/'work/build24c'),str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from patch import reseal
from runtime import harden_kit
from student_pilot.source_seal import inventory
tree=inventory(L/'work/tree_r1');assert tree==J.load(L/'work/build24b/TREE_FILES.json')
records={}
for name in ('q','n'):
 k=L/'work/build24/kits'/name;old=L/'attic/build24d/work/build24/kits'/name
 for p in (k/'k').iterdir():
  if p.name!='j.json':assert p.read_bytes()==(old/'k'/p.name).read_bytes(),p
 assert (k/'b/g.py').read_bytes()==(old/'b/g.py').read_bytes()
 target=D/'generated'/name;target.parent.mkdir(exist_ok=True);shutil.copytree(old,target)
 harden_kit(target);seal=reseal(target)
 assert seal==J.seal(k),(name,seal,J.seal(k))
 before={str(p.relative_to(target)):J.sha(p) for p in target.rglob('*') if p.is_file()};harden_kit(target)
 assert before=={str(p.relative_to(target)):J.sha(p) for p in target.rglob('*') if p.is_file()}
 records[name]=dict(seal=seal,regeneration_identical=True,idempotent=True,config_bytes_unchanged=True)
packages={p.name:dict(bytes=p.stat().st_size,sha256=J.sha(p)) for p in (L/'out').glob('tree_rebuild_b24*.tar')}
assert packages['tree_rebuild_b24c_22859833.tar']['sha256']=='457fe75df9ee44b72c5caf95b4c4c06ec8081057916f27dbf54f4da12b081f4f'
assert packages['tree_rebuild_b24b_7d7a8858.tar']['sha256']=='4bfb9f759f505276cc908be8885942822edb53b7c048adda0e6ae1c171366f01'
J.write(D/'INVARIANTS.json',dict(status='PASS',tree_byte_identical=True,kits=records,packages=packages))
