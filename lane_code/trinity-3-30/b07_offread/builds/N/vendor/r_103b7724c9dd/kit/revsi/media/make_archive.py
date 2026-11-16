"""Operator-only single-pass, 8 MB/s NFS reader; deterministic exact media tar."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import time
from check_on_orchard import manifest


class Reader:
    def __init__(self,stream,rate):
        self.stream=stream;self.rate=rate;self.start=time.monotonic();self.size=0;self.hash=hashlib.sha256()
    def read(self,n=-1):
        raw=self.stream.read(n);self.size+=len(raw);self.hash.update(raw)
        if self.rate:
            wait=self.size/self.rate-(time.monotonic()-self.start)
            if wait>0:time.sleep(wait)
        return raw


class Writer:
    def __init__(self,stream):self.stream=stream;self.size=0;self.hash=hashlib.sha256()
    def write(self,raw):self.size+=len(raw);self.hash.update(raw);return self.stream.write(raw)
    def tell(self):return self.size
    def flush(self):return self.stream.flush()


def build(need,output,rate=8_000_000):
    rows=manifest(need);output=Path(output)
    if not output.resolve().is_relative_to('/scratch'):raise ValueError('Archive output must be on /scratch')
    with output.open('xb') as stream:
        writer=Writer(stream)
        with tarfile.open(fileobj=writer,mode='w|',format=tarfile.USTAR_FORMAT) as archive:
            for row in sorted(rows,key=lambda r:r['relative_path']):
                path=Path(row['source'])
                if path.is_symlink() or not path.is_file() or path.stat().st_size!=row['bytes']:raise ValueError('Source size/type differs: '+str(path))
                item=tarfile.TarInfo(row['relative_path']);item.size=row['bytes'];item.mode=0o644;item.mtime=0;item.uid=item.gid=0;item.uname=item.gname=''
                with path.open('rb') as source:
                    reader=Reader(source,rate);archive.addfile(item,reader)
                    if reader.read(1) or reader.size!=row['bytes'] or reader.hash.hexdigest()!=row['sha256']:
                        raise ValueError('Source pin differs: '+str(path))
        return dict(files=len(rows),bytes=writer.size,sha256=writer.hash.hexdigest(),archive=str(output))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--need',default=str(Path(__file__).with_name('NEED_261.json')));p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(build(a.need,a.output),sort_keys=True))
