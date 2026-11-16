"""Authenticated local bootstrap."""
import hashlib
import json
import os
import datetime as dt
from pathlib import Path
import sys
import tarfile


def resolve_inputs(request,directory):
    for spec in request['datasets']:
        for key in ('rows','membership','slice_membership','indices','videos'):
            if spec.get(key,{}).get('path','').startswith('$Q/'):
                spec[key]['path']=str(directory/spec[key]['path'][3:])


def main():
    root=Path(sys.argv[1])
    work=Path(sys.argv[2])
    auth=json.loads((root/'k/2.json').read_text())
    if auth['build_only'] or dt.datetime.now(dt.timezone.utc).timestamp()>=dt.datetime.fromisoformat(auth['until'].replace('Z','+00:00')).timestamp():
        raise ValueError('E00')
    for line in (root/'SHA256SUMS.txt').read_text().splitlines():
        expected,name=line.split('  ',1)
        path=root/name
        if not path.resolve().is_relative_to(root.resolve()):raise ValueError('E01')
        with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=expected:raise ValueError('E02')
    for source,dest in (('k/0.tar','b'),('k/1.tar','q')):
        out=work/dest;out.mkdir(parents=True,exist_ok=True)
        with tarfile.open(root/source) as tf:
            for m in tf.getmembers():
                if Path(m.name).is_absolute() or '..' in Path(m.name).parts or not m.isfile():raise ValueError('E03')
            tf.extractall(out,filter='data')
    request=json.loads((work/'q/0.json').read_text())
    resolve_inputs(request,work/'q')
    (work/'q/0.json').write_text(json.dumps(request)+'\n')
    sys.path.insert(0,str(work/'b'))
    from launch import main as run
    run(str(work/'q/0.json'),str(work))


if __name__=='__main__':main()
