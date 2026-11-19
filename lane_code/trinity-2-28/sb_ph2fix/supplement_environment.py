"""Stage the reader's SciPy dependency from the existing local Python 3.12 CPU environment."""
import hashlib
import json
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
SOURCE=Path('/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages')
DEST=ROOT/'payload/environment/lib/python3.12/site-packages'


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()


def main():
    rows=[];pins={str(Path(__file__)):sha(Path(__file__))}
    for name in ('scipy','scipy.libs','scipy-1.14.1.dist-info'):
        folder=SOURCE/name
        if not folder.is_dir(): raise SystemExit('MISSING '+str(folder))
        for p in sorted(folder.rglob('*')):
            if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.pyc': continue
            dest=DEST/p.relative_to(SOURCE);dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,dest)
            digest=sha(dest);pins[str(p)]=digest
            rows.append(dict(path=str(p),staged_path=str(dest.relative_to(ROOT)),roles=['sam_environment','reader_environment_dependency'],
                             bytes=dest.stat().st_size,sha256=digest,status='PASS'))
    result=dict(status='PASS',package='scipy 1.14.1 (CPython 3.12)',command='python -B supplement_environment.py',
                files=len(rows),bytes=sum(r['bytes'] for r in rows),inventory=rows,input_sha256=pins)
    (ROOT/'out/ENV_SUPPLEMENT.json').write_text(json.dumps(result,indent=1)+'\n')
    print('SciPy staged:',result['files'],'files',result['bytes'],'bytes')

if __name__=='__main__':main()
