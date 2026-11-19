import json,os,shutil
from pathlib import Path
L=Path(__file__).resolve().parents[2];sizes={}
for name,root in [('lane',L),('tmp',L/'work/tmp')]:
    total=0;pending=[root]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for e in entries:
                if e.is_symlink():continue
                if e.is_dir(follow_symlinks=False):pending.append(e.path)
                elif e.is_file(follow_symlinks=False):total+=e.stat(follow_symlinks=False).st_size
    sizes[name]=total
sizes['scratch_free_bytes']=shutil.disk_usage('/scratch').free
assert sizes['lane']<7_000_000_000 and sizes['tmp']<200_000_000
assert sizes['scratch_free_bytes']>=85*1024**3
(L/'work/build_n1/STORAGE.json').write_text(json.dumps(sizes,indent=2)+'\n')
print(json.dumps(sizes))
