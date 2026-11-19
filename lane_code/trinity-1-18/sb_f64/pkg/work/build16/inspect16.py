from pathlib import Path
import os,json,shutil
L=Path(__file__).resolve().parents[2];B=L/'work/build16'
(L/'work/tmp').mkdir(exist_ok=True)
size=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())
assert size<1_500_000_000
(B/'BASE15_SEAL.json').write_bytes((L/'out/TREE_SEAL.json').read_bytes())
(B/'run.sh').write_bytes((L/'work/build15/run.sh').read_bytes())
(B/'STATUS.md').write_text('# Build 16 status\n\nGO=false. Inspecting pinned authorities and preparing the new N inputs.\n')
print('storage',size,shutil.disk_usage('/scratch').free)
root=Path('/scratch/jjyeung/n30_mirror')
for base,dirs,files in os.walk(root):
    depth=len(Path(base).relative_to(root).parts)
    if depth>=6:dirs[:]=[]
    for name in files:
        if any(x in name.lower() for x in ('k1','r0','rooms','alias','token_map','elig.py')):
            p=Path(base)/name
            print(p,p.stat().st_size)
cfg=json.loads((L/'work/build15/inputs/kit_config.json').read_text())
print('config_keys',list(cfg))
print('prior_config', (L/'work/build15/inputs/config.json').read_text()[:1200])
