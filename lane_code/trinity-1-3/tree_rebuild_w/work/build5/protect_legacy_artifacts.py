"""Prevent legacy tests from creating scratch products beside the working source."""
import json
import os
from pathlib import Path
import stat
L=Path(__file__).resolve().parents[2]
root=L/'work/tree_r1/artifacts'
rows=[]
if root.exists():
    for directory,dirs,files in os.walk(root,topdown=False,followlinks=False):
        for path in [*(Path(directory)/name for name in files),Path(directory)]:
            if path.is_symlink():continue
            mode=stat.S_IMODE(path.stat().st_mode)
            path.chmod(mode & ~0o222)
            rows.append(dict(path=str(path.relative_to(L)),prior_mode=mode,mode=mode & ~0o222))
output=L/'work/build5/proofs/artifact_locations';output.mkdir(parents=True,exist_ok=True)
(output/'PROTECTION.json').write_text(json.dumps(dict(
    reason='Legacy source-relative artifacts must not be written outside work/tmp; final tests execute the extracted package there.',
    paths=rows),indent=2)+'\n')
print(json.dumps(dict(protected_paths=len(rows),source=str(root.relative_to(L)))))
