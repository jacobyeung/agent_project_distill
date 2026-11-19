"""Run manually on the login host to place the delivered files in N's pool folder."""
from pathlib import Path
import hashlib,json,shutil,sys
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def main(source,destination):
    source=Path(source).resolve();destination=Path(destination).resolve()
    if destination!=Path('/project/community/jjyeung/okh7/x_22c714e1'):raise ValueError('E01')
    value=json.loads((source/'work/build21/UPLOADS.json').read_text());rows=[]
    for entry in value['files']:
        name=Path(entry['opaque_name'])
        if name.is_absolute() or '..' in name.parts:raise ValueError('E02')
        local=(source/'work/build21/kits'/name) if name.parts[0]=='q' else source/'work/build21/upload'/name
        if not local.is_file() or local.stat().st_size!=entry['bytes'] or sha(local)!=entry['sha256']:raise ValueError('E03:'+str(name))
        rows.append((local,destination/name,entry))
    for local,target,entry in rows:
        if target.exists():
            if target.stat().st_size!=entry['bytes'] or sha(target)!=entry['sha256']:raise ValueError('E04:'+str(target))
            continue
        target.parent.mkdir(parents=True,exist_ok=True)
        with local.open('rb') as a,target.open('xb') as b:shutil.copyfileobj(a,b,8<<20)
        if sha(target)!=entry['sha256']:raise ValueError('E05')
    print(json.dumps(dict(files=len(rows),bytes=value['total_bytes'])))
if __name__=='__main__':main(*sys.argv[1:])
