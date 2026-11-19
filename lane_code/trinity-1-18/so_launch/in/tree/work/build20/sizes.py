from pathlib import Path
L=Path(__file__).resolve().parents[2]
for build in ('build19','build20'):
    for folder in ('proofs/final/frozen','proofs/final/suite_tree','proofs/final/packet','proofs/final_focused','proofs/native','proofs/mutations','kits'):
        root=L/'work'/build/folder
        print(build,folder,sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink()))
