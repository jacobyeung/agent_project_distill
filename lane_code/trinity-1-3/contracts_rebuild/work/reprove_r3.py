"""Reuse proof destinations by restoring exact sealed preimages; retain added files."""
from pathlib import Path
import json,tarfile,subprocess,sys
L=Path(__file__).resolve().parents[1];B=L/'work/base/work/base/tree_b01ce449';O=L/'out'
manifest=json.loads((O/'PATCH_MANIFEST_R3.json').read_text())
stash=L/'work/proof_preimages_r3';stash.mkdir()
targets=[('base',L/'work/trees/r3_proof/base'),('snapshot',L/'work/trees/r3_snapshot')]
with tarfile.open(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar') as archive:
    members={m.name:m for m in archive if m.isfile()}
    for kind,target in targets:
        for rel in manifest['files']:
            source=B/rel
            member=members.get('tree_r1/'+rel) if kind=='snapshot' else None
            original=(archive.extractfile(member).read() if member else None) if kind=='snapshot' else (source.read_bytes() if source.exists() else None)
            dest=target/rel
            if original is None:
                if dest.exists():
                    saved=stash/kind/rel;saved.parent.mkdir(parents=True,exist_ok=True);dest.rename(saved)
            else:dest.write_bytes(original)
        target.chmod(0o555 if kind=='base' else 0o755)
p=L/'work/apply_proof_r3.py';s=p.read_text()
s=s.replace("root.mkdir();target=root/'base';shutil.copytree(B,target)","root.mkdir(exist_ok=True);target=root/'base';assert inv(target)==inv(B)")
s=s.replace('snapshot.mkdir()','snapshot.mkdir(exist_ok=True)')
s=s.replace('full_tree_copies=4','full_tree_copies=5')
(L/'work/apply_proof_final_r3.py').write_text(s)
subprocess.run(['/scratch/jjyeung/envs/p1cpu/bin/python','-I','-s','-B',str(L/'work/apply_proof_final_r3.py')],check=True)
