"""Verify and unpack one export archive into a fresh local directory."""
import argparse,shutil,sys,tarfile
from pathlib import Path,PurePosixPath
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def receive(archive,expected,dest):
    archive=local(archive);dest=local(dest)
    if sha(archive)!=expected:raise ValueError('Archive hash differs')
    if dest.exists():raise ValueError('Destination exists; preserve it and select a fresh directory')
    with tarfile.open(archive,'r:*') as tar:
        members=tar.getmembers();names=set();size=0
        if len(members)>10000:raise ValueError('Unexpected archive member count')
        for m in members:
            name=PurePosixPath(m.name)
            if name.is_absolute() or '..' in name.parts or not (m.isfile() or m.isdir()):raise ValueError('Unsafe archive member')
            if name.as_posix() in names:raise ValueError('Duplicate archive member')
            names.add(name.as_posix());size+=m.size
        if size>100*1024**3:raise ValueError('Export archive exceeds 100 GiB')
        dest.mkdir(parents=True)
        for m in members:
            p=dest/m.name
            if m.isdir():p.mkdir(parents=True,exist_ok=True)
            else:
                p.parent.mkdir(parents=True,exist_ok=True)
                with tar.extractfile(m) as source,p.open('xb') as target:shutil.copyfileobj(source,target,length=1024*1024)
    result=dict(archive=pin(archive),destination=str(dest),members=len(members),bytes=size,
        scope='Archive integrity only; export_check must authenticate artifact and tensor inventory')
    dump(dest/'LEGS1_RECEIVE.json',result);return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','sha256','dest'):p.add_argument('--'+name,required=True)
    a=p.parse_args();print(json.dumps(receive(a.archive,a.sha256,a.dest)))
if __name__=='__main__':main()
