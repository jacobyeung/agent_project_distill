from pathlib import Path
import datetime,hashlib,json,shutil,subprocess
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21e';A=L/'attic/build21e'
D.mkdir(exist_ok=True);A.mkdir(parents=True,exist_ok=True)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
subprocess.run(['date','-u'],check=True)
start=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),workspace_bytes=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink()),
    bases=[dict(path=str(p.relative_to(L)),bytes=p.stat().st_size,sha256=sha(p)) for p in (L/'out/tree_rebuild_b21c_6f5e6cc2.tar',L/'out/tree_rebuild_b21d_a75e1b0a.tar')],
    kit_files={str(p.relative_to(B/'kits/q')):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in (B/'kits/q').rglob('*') if p.is_file()},
    kit_seal=sha(B/'kits/q/SHA256SUMS.txt'),tree=json.loads((L/'out/TREE_SEAL.json').read_text()))
for n in ('kit.py','joblib.py','jobtest.py','OPERATOR.md','PACKAGE_MANIFEST.json','UPLOADS.json','FINAL_KITS.json','DELIVERY.json'):
    if not (A/n).exists():shutil.copyfile(B/n,A/n)
(D/'START.json').write_text(json.dumps(start,indent=2)+'\n')
print(json.dumps(dict(workspace_bytes=start['workspace_bytes'],kit_seal=start['kit_seal']),indent=2))
