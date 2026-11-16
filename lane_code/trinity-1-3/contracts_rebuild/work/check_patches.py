from pathlib import Path
import subprocess
import shutil
import json
import hashlib
L=Path(__file__).resolve().parents[1]
base=L/'work/base/work/base/tree_b01ce449'
tag=__import__('sys').argv[1]
def fresh(name):
    p=L/'work/trees'/f'{name}_{tag}'
    shutil.copytree(base,p)
    p.chmod(0o755)
    for f in p.rglob('*'):f.chmod(0o755 if f.is_dir() else 0o644)
    return p
report={}
for group in ('geometry','candidates','box'):
    tree=fresh('apply_'+group)
    r=subprocess.run(['patch','--dry-run','--fuzz=0','-p1','-i',str(L/f'out/PATCH_{group}.diff')],cwd=tree,text=True,capture_output=True)
    report[group]=dict(returncode=r.returncode,output=r.stdout+r.stderr)
    assert r.returncode==0,report[group]
tree=fresh('apply_ordered')
for group in ('geometry','candidates','box'):
    command=['patch','--fuzz=0','-p1','-i',str(L/f'out/PATCH_{group}.diff')]
    dry=subprocess.run(command+['--dry-run'],cwd=tree,text=True,capture_output=True)
    r=subprocess.run(command,cwd=tree,text=True,capture_output=True)
    report['ordered_'+group]=dict(dry_returncode=dry.returncode,returncode=r.returncode,output=r.stdout+r.stderr)
    assert dry.returncode==r.returncode==0
manifest=json.loads((L/'out/PATCH_MANIFEST.json').read_text())
for name,entry in manifest['files'].items():
    assert hashlib.sha256((tree/name).read_bytes()).hexdigest()==entry['patched_sha256']
    if entry['base_sha256']:
        assert hashlib.sha256((base/name).read_bytes()).hexdigest()==entry['base_sha256']
report['hashes_verified']=True
(L/'out/PATCH_APPLICATION.json').write_text(json.dumps(report,indent=2))
print('All individual and ordered patch checks pass with fuzz disabled.')
