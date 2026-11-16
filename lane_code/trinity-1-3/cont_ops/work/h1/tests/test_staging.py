import hashlib,importlib.util,io,json,tarfile
from pathlib import Path
H=Path(__file__).resolve().parents[1];root=H/'evidence/staging_test';(root/'k').mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('stage',H/'tools/staging_check.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def sha(b):return hashlib.sha256(b).hexdigest()
base={'extra':[],'tars':[]};(root/'base.json').write_text(json.dumps(base))
b=b'verified bytes\n';tar=root/'new.tar'
with tarfile.open(tar,'w') as f:
 t=tarfile.TarInfo('ap/12345678/a');t.size=len(b);f.addfile(t,io.BytesIO(b))
cur={'extra':[],'tars':[dict(parts=[str(tar)],files={'ap/12345678/a':sha(b)},sha256=m.sha(tar))]};(root/'k/0.json').write_text(json.dumps(cur))
assert not m.main(root,root/'base.json')['missing']
cur['tars'][0]['files']['ap/12345678/a']='0'*64;(root/'k/0.json').write_text(json.dumps(cur))
try:m.main(root,root/'base.json')
except ValueError:pass
else:raise AssertionError('corruption accepted')
(root/'result.json').write_text('{"status":"PASS","checks":["streaming tar digest and member pins","corrupt member refused"]}\n')
print('staging tests passed')
