from pathlib import Path
import json,os,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3'
pending=[L];sizes={};total=0;files=0
while pending:
    with os.scandir(pending.pop()) as entries:
        for entry in entries:
            if entry.is_symlink():continue
            if entry.is_dir(follow_symlinks=False):pending.append(Path(entry.path))
            elif entry.is_file(follow_symlinks=False):
                size=entry.stat().st_size;total+=size;files+=1
                rel=Path(entry.path).relative_to(L);key='/'.join(rel.parts[:3]);sizes[key]=sizes.get(key,0)+size
v=dict(bytes=total,files=files,by_folder=sizes,limit_bytes=8*1024**3)
(B/'STORAGE.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps(dict(bytes=total,files=files,largest=sorted(sizes.items(),key=lambda x:x[1],reverse=True)[:8])))
assert total<=8*1024**3
