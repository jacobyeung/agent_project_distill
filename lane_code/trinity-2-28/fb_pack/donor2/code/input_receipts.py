from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parents[1];p=W.parent/'donor/out/TREE_SEAL.json';raw=p.read_bytes();d=json.loads(raw)
d.update(input_sha256={str(p):hashlib.sha256(raw).hexdigest(),str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},command='python code/input_receipts.py')
(W/'out/TREE_SEAL.json').write_text(json.dumps(d,indent=2)+'\n')
