from common import *
import shutil
paths=['work/build22/kits/q/k/n.json','work/build24m2c/UPLOADS_q.json','work/build24m2c/UPLOADS_n.json',
       'attic/build24b/kit_n','attic/build24b/work/build24/kits/q/b/g.py','work/build21/kit.py',
       'work/build24/WITNESS200.json','work/build24/proofs/resolver/f/pool','work/build24/proofs/resolver/f/l.json']
records=[]
for rel in paths:
 src=W/'w24'/rel;dst=L/rel
 if dst.exists():continue
 if not src.exists():records.append(dict(path=rel,status='MISSING'));continue
 dst.parent.mkdir(parents=True,exist_ok=True)
 if src.is_dir():shutil.copytree(src,dst)
 else:shutil.copyfile(src,dst)
 records.append(dict(path=rel,status='copied retained fixture',source=str(src)))
J.write(D/'FIXTURE_INPUTS.json',records)
print(records)
