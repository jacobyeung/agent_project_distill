from pathlib import Path
import ast, json, shutil, sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24d';A=L/'attic/build24d'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from launch_r2.build import capsule_json

def preserve(p):
    dest=A/p.relative_to(L);dest.parent.mkdir(parents=True,exist_ok=True)
    assert not dest.exists();p.rename(dest)
    if dest.is_dir():shutil.copytree(dest,p)
    else:shutil.copyfile(dest,p)

def reseal(k,go=False):
    files={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
    (k/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(files.items())))
    b=J.load(k/'BUILD.json');b.update(GO=go,kit_sha256=J.seal(k));(k/'BUILD.json').write_bytes(capsule_json(b))
    return J.seal(k)

def main():
    for name in ('q','n'):preserve(L/'work/build24/kits'/name)
    p=L/'work/build24/joblib.py';preserve(p);s=p.read_text()
    start=s.index('def small_archive(');end=s.index('\ndef metadata_at',start)
    replacement=(D/'selection.py').read_text()
    s=s[:start]+replacement+'\n'+s[end:]
    s=s.replace("values,metadata=small_archive(milestone/'s.tar')", "values,metadata=small_archive(milestone/'s.tar',roots=[receipt['pins'],spec['p_kit_config'],load(kit/'k/n.json')])")
    s=s.replace("    safe=name_guard(kit)\n    root.mkdir", "    if spec.get('step',400)==400:\n        for item in resolved['small_files'].values():\n            selected400(item.get('original',item.get('member','')))\n            selected400(item.get('member',''))\n        for pin in load(resolved['receipt']['path'])['pins'].values():selected400(pin['path'])\n    safe=name_guard(kit)\n    root.mkdir")
    s=s.replace("            safe(member.name)\n            path=inside(export", "            if spec.get('step',400)==400:selected400(member.name)\n            safe(member.name)\n            path=inside(export")
    p.write_text(s);ast.parse(s)
    for name in ('q','n'):
        k=L/'work/build24/kits'/name;(k/'b/z.py').write_text(s);reseal(k)
    J.write(D/'PATCH.json',dict(kits=['q','n'],tree_changed=False,old_resolver=str(A/'work/build24/joblib.py')))

if __name__=='__main__':main()
