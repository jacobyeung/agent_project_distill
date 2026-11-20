F=/scratch/jjyeung/orch_n30/fb_pack; C=$F/combo; cd $C/X
for p in patchA2/out/PATCH_A2.patch donor3/out/PATCH_DONOR3.patch camform2/out/PATCH_CAMFORM2_ON_A2.patch; do echo "== $p"; if patch -p1 --fuzz=0 --dry-run < $F/$p > $C/dry_$(basename $p).log 2>&1; then patch -p1 --fuzz=0 < $F/$p > $C/apply_$(basename $p).log 2>&1; echo "applied rc=$?"; grep -i "offset\|fuzz\|fail" $C/apply_$(basename $p).log; else echo DRYFAIL; grep -i -B2 "fail" $C/dry_$(basename $p).log; break; fi; done
find . -name '*.orig' -o -name '*.rej' | head
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'P'
import sys; sys.path.insert(0,'/scratch/jjyeung/orch_n30/fb_pack/combo/X')
import hashlib,json,os
from pathlib import Path
try:
  from student_pilot import source_seal, p3_provenance
  inv=source_seal.inventory(Path('/scratch/jjyeung/orch_n30/fb_pack/combo/X'))
  print('inventory type',type(inv).__name__, len(inv) if hasattr(inv,'__len__') else '')
except Exception as e: print('seal fn err',repr(e)[:300]); inv=None
root=Path('/scratch/jjyeung/orch_n30/fb_pack/combo/X')
files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
print('files',len(files),'hash',hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest())
P
