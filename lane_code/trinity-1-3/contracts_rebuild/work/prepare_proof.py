from pathlib import Path
import json
import shutil
L=Path(__file__).resolve().parents[1]
base=L/'work/base/work/base/tree_b01ce449'
files=[p for p in base.rglob('*') if p.is_file()]
sizes=[p.stat().st_size for p in files]
assert max(sizes)<20_000_000
assert sum(sizes)<50_000_000
manifest=json.loads((L/'out/PATCH_MANIFEST.json').read_text())
modules=[n[:-3].replace('/','.') for n in manifest['files'] if (base/n).exists()]
tests=[]
for p in files:
    if p.name.startswith('test') and p.suffix=='.py':
        text=p.read_text()
        if any(m in text or (f'from {m.rpartition(".")[0]} import' in text and m.rpartition('.')[2] in text) for m in modules):
            tests.append(str(p.relative_to(base)))
(L/'work/base_tests.json').write_text(json.dumps(tests,indent=2))
for name in ('base_proof','patched'):
    target=L/'work/trees'/name
    if not target.exists():
        shutil.copytree(base,target)
    target.chmod(0o755)
    for p in target.rglob('*'):
        p.chmod(0o755 if p.is_dir() else 0o644)
    if name=='patched':
        for rel in manifest['files']:
            p=target/rel
            p.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(L/'work/src'/rel,p)
print(dict(base_bytes=sum(sizes),base_files=len(files),selected_tests=tests))
