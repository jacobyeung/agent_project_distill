import json,subprocess,sys
from pathlib import Path
b=Path('/project/community/jjyeung/okh7/i_@STORE@');h=b.parent/'x_3fdda0fb';k=b.parent/'x_@STORE@'
assert not k.exists() and not k.is_symlink(), 'KH must be absent'
# FIX6 separates read-only evidence validation from allocation-time g.check.
# Refuse any deriver that is not byte-identical to the frozen final archive.
import hashlib
if (b/'d.py').is_symlink():raise SystemExit('REFUSED: linked deriver')
if hashlib.sha256((b/'d.py').read_bytes()).hexdigest()!='@DERIVER@':
 raise SystemExit('REFUSED: d.py SHA differs from final archive')

assert (b/'e0/rc').read_text().strip()=='0'
with (b/'compare.json').open('x') as f:
 subprocess.run([sys.executable,'-B',str(b/'d.py'),'--source',str(h),'--source-manifest-sha256','@SOURCE_MANIFEST@','--packet',str(b),'--bundle',str(b),'--out',str(k),'--selection-evidence',str(b/'q/q.json'),'--evidence',str(b/'e')],stdout=f,check=True)
d=json.loads((b/'compare.json').read_text());assert d['status']=='READY' and d['missing_source_members']==[]
(k/'o').mkdir(mode=0o700,exist_ok=True)
print(json.dumps(d,sort_keys=True));print('READY; CPU proof only; production GO remains false')
