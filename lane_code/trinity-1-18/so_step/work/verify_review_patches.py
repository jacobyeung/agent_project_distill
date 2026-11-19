"""Apply the ordered series to a fresh bounded copy of only touched input files."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'out/patches/manifest.json').read_text())
base=ROOT/'in/tree/work/tree_r1'
destination=ROOT/'work'/sys.argv[1]
destination.mkdir()
paths=sorted({p for name,item in manifest.items() if name.endswith('.diff') for p in item['paths']})
for relative in paths:
    source=base/relative
    if source.exists():
        target=destination/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(source.read_bytes())
for name,item in manifest.items():
    if not name.endswith('.diff'): continue
    path=ROOT/'out/patches'/name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
    assert path.stat().st_size==item['bytes']
    result=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(path)],cwd=destination,
                          text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    print('$ patch --batch --fuzz=0 -p1 -i '+str(path))
    print(result.stdout,end='')
    print('EXIT='+str(result.returncode))
    assert result.returncode==0
for relative in paths:
    target=destination/relative
    assert target.read_bytes()==(ROOT/'work/tree'/relative).read_bytes(),relative
    ast.parse(target.read_text(),filename=relative)
print(f'PATCH_PROOF: four ordered patches apply without fuzz; all {len(paths)} touched files match work/tree exactly')
# Account for every file in the input and review trees without copying untouched files.
extra=[]
for source in sorted((ROOT/'work/tree').rglob('*')):
    if not source.is_file(): continue
    relative=str(source.relative_to(ROOT/'work/tree'))
    if relative in paths: continue
    assert (base/relative).is_file(),relative
    assert source.read_bytes()==(base/relative).read_bytes(),relative
    extra.append(relative)
for source in base.rglob('*'):
    if source.is_file(): assert (ROOT/'work/tree'/source.relative_to(base)).is_file()
print(f'UNCHANGED_PROOF: remaining {len(extra)} files equal input; no input files missing')
for folder in ('kit_profile','kit_timing'):
    for path in sorted((ROOT/'out'/folder).glob('*.py')):
        ast.parse(path.read_text(),filename=str(path))
    for path in sorted((ROOT/'out'/folder).glob('*.sh')):
        subprocess.run(['bash','-n',str(path)],check=True)
print('KIT_SYNTAX: all Python and shell files pass')
