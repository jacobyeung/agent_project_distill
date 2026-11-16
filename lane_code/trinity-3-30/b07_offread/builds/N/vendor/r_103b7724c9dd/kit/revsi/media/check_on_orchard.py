"""Verify an extracted tier-32 root using only the Python standard library."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def manifest(path):
    rows=json.loads(Path(path).read_text());seen=set()
    for row in rows:
        name=PurePosixPath(row['relative_path'])
        if name.is_absolute() or '..' in name.parts or len(name.parts)!=1 or name.suffix!='.mp4' or str(name) in seen:
            raise ValueError('Unsafe or duplicate media member')
        if type(row['bytes']) is not int or row['bytes']<=0 or len(row['sha256'])!=64:raise ValueError('Invalid media pin')
        seen.add(str(name))
    return rows


def check(root,need):
    root=Path(root).resolve();rows=manifest(need)
    observed={p.name for p in root.iterdir()}
    if observed!={r['relative_path'] for r in rows}:raise ValueError('Extracted membership differs')
    for row in rows:
        path=root/row['relative_path']
        if path.is_symlink() or not path.is_file():raise ValueError('Require regular media file')
        h=hashlib.sha256();size=0
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):h.update(block);size+=len(block)
        if size!=row['bytes'] or h.hexdigest()!=row['sha256']:raise ValueError('Media pin differs: '+path.name)
    return dict(verified=True,files=len(rows),bytes=sum(r['bytes'] for r in rows))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--need',default=str(Path(__file__).with_name('NEED_261.json')))
    p.add_argument('--emit-script',action='store_true',help='Print a self-contained stdlib verification script for stdin transport')
    a=p.parse_args()
    if a.emit_script:
        rows=manifest(a.need)
        print("import json; ns={'__name__':'checker'}; exec("+repr(Path(__file__).read_text())+",ns)")
        print("ns['manifest']=lambda unused: "+repr(rows))
        print("print(json.dumps(ns['check']("+repr(a.root)+",None),sort_keys=True))")
    else:print(json.dumps(check(a.root,a.need),sort_keys=True))
