import json,subprocess,sys
from pathlib import Path
b=Path('/project/community/jjyeung/okh7/i_@STORE@');h=b.parent/'x_3fdda0fb';k=b.parent/'x_@STORE@'
assert not k.exists() and not k.is_symlink(), 'KH must be absent'
# Evidence validation runs before allocation-time admission.
# Refuse any deriver that is not byte-identical to the frozen final archive.
import hashlib
if (b/'d.py').is_symlink():raise SystemExit('REFUSED: linked deriver')
if hashlib.sha256((b/'d.py').read_bytes()).hexdigest()!='@DERIVER@':
 raise SystemExit('REFUSED: d.py SHA differs from final archive')

for name in ('n.json','records/n.json'):
 if hashlib.sha256((b/name).read_bytes()).hexdigest()!='@REMOVE_SHA256@':
  raise SystemExit('REFUSED: REMOVE list SHA differs from packet C')
cfg=json.loads((b/'config.json').read_text())
assert cfg['remove_files'][-1]==dict(path='@REMOVE_PATH@',sha256='@REMOVE_SHA256@')
assert (b/'e0/rc').read_text().strip()=='0'
with (b/'compare.json').open('x') as f:
 subprocess.run([sys.executable,'-B',str(b/'d.py'),'--source',str(h),'--source-manifest-sha256','@SOURCE_MANIFEST@','--packet',str(b),'--bundle',str(b),'--out',str(k),'--selection-evidence',str(b/'q/q.json'),'--evidence',str(b/'e')],stdout=f,check=True)
d=json.loads((b/'compare.json').read_text());assert d['status']=='READY' and d['missing_source_members']==[]
cur=json.loads((k/'k/0.json').read_text())
rows=[x for x in cur['extra'] if x.get('dest')=='@REMOVE_PATH@']
assert rows==[dict(dest='@REMOVE_PATH@',parts=[str(b/'n.json')],sha256='@REMOVE_SHA256@')]
(k/'o').mkdir(mode=0o700,exist_ok=True)
print('PASS REMOVE n.json SHA @REMOVE_SHA256@; staged for packet C');print(json.dumps(d,sort_keys=True));print('READY; CPU proof only; production GO remains false')
