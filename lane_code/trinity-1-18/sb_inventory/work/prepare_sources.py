"""Snapshot only the named sealed source tree and configurations into this workspace."""
import hashlib,json,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
A=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/out/tree_rebuild_b19_8ea1fe6b.tar')
def pin(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
dest=R/'work/sealed'
with tarfile.open(A) as t:
    members=t.getmembers()
    (R/'work/archive_members.txt').write_text('\n'.join(m.name for m in members))
    for m in members:
        if m.isfile() and (m.name.startswith(('work/tree_r1/','work/n1fix2/inputs/')) or m.name in (
            'out/TREE_SEAL.json','out/BUILD19_REPORT.md','work/build19/inputs/config.json','work/build19/inputs/kit_config.json')):
            p=dest/m.name
            assert p.resolve().is_relative_to(dest.resolve())
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(m).read())
seal=json.loads((dest/'out/TREE_SEAL.json').read_text())
bad=[n for n,h in seal['files'].items() if pin(dest/'work/tree_r1'/n)['sha256']!=h]
assert not bad
result=dict(schema='sb-package-selection-v1',selected='w19',archive_members=len(members),
    sealed_tree_files=len(seal['files']),mismatches=bad,tree_sha256=seal['tree_sha256'],
    inputs=[pin(A),pin(dest/'out/TREE_SEAL.json'),pin(dest/'out/BUILD19_REPORT.md'),pin(Path(__file__))])
(R/'out/PACKAGE.json').write_text(json.dumps(result,indent=2)+'\n')
print('sealed tree files',len(seal['files']),'mismatches',len(bad))
