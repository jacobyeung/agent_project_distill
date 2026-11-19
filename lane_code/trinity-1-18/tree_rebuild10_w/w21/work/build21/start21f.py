from pathlib import Path
import datetime,hashlib,json,shutil,subprocess
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21f';A=L/'attic/build21f'
D.mkdir(exist_ok=True);A.mkdir(parents=True,exist_ok=True)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for raw in iter(lambda:f.read(1<<20),b''):h.update(raw)
    return h.hexdigest()
subprocess.run(['date','-u'],check=True)
kit={str(p.relative_to(B/'kits/q')):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in (B/'kits/q').rglob('*') if p.is_file()}
seal=sha(B/'kits/q/SHA256SUMS.txt')
assert seal=='5d300f192c97134c441696df0ab09435e2ad15be879603b230e6cd0c5d615522'
start=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),kit_seal=seal,kit_files=kit,
    workspace_bytes=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink()),
    bases=[dict(path=str(p.relative_to(L)),bytes=p.stat().st_size,sha256=sha(p)) for p in
        [L/'out/tree_rebuild_b21e_ac8fa8e3.tar',L/'out/BUILD21E_REPORT.md']],
    tree=json.loads((L/'out/TREE_SEAL.json').read_text()))
for n in ('naming21.py','PACKAGE_MANIFEST.json'):
    target=A/n
    assert not target.exists()
    shutil.copyfile(B/n,target)
(D/'START.json').write_text(json.dumps(start,indent=2)+'\n')
print(json.dumps(dict(kit_seal=seal,workspace_bytes=start['workspace_bytes'])))
