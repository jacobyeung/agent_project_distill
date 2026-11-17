from pathlib import Path
import hashlib,json,sys
W=Path.cwd();sys.path.insert(0,str(W/'work/p'))
from orchard_h10.build import build
import shutil
source=W/'work/reader_repin'
shutil.copytree(W/'work/p/b/e2e_reader',source/'e2e_reader',dirs_exist_ok=True)
spec=dict(source=str(source),sha256={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()})
repin=W/'work/reader_repin.json';repin.write_text(json.dumps(spec))
for token,rule in [('c4d7e0a91b28f','null_argmax'),('d8a2f6c09e137','candidates_argmax')]:
 print(build(W/'out'/token,token,True,str(repin),rule))
