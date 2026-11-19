"""Create an authenticated local A10b asset copy for the additive adapter patch."""
import argparse
from pathlib import Path
import shutil
import sys
import tarfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common228 import *

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input-A10b',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();source=Path(a.input_A10b).resolve();dest=local(a.out)
    pins=read(HERE/'A10b_PINS.json')
    # Authenticate the effective input metadata before publishing the copy.
    chosen=dict((name,source/'package'/name) for name in pins['package'])
    chosen['a/1.json']=source/'package/a/1.json'
    chosen['a/export.json']=source/'package/a/export.json'
    for name,path in chosen.items():checked(path,pins['package'][name])
    if dest.exists():raise Refusal('Bootstrap destination exists; use a fresh directory')
    dest.mkdir(parents=True)
    for name,path in chosen.items():
        target=dest/'package'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    for name in ('tower_sequence.py','unpack_return.py','fetch_return.py'):
        checked(source/name,pins['operators'][name])
        shutil.copyfile(source/name,dest/name)
    if sha(dest/'tower_sequence.py')!=pins['operator_sha256']:raise Refusal('Operator pin differs')
    total=0
    with tarfile.open(dest/'package/0.tgz') as archive:
        for member in archive:
            if member.name not in pins['source'] or not member.isfile():raise Refusal('Unexpected source member')
            total+=member.size
            if total>32*1024**2:raise Refusal('Payload expansion exceeds package allowance')
            target=dest/'src'/member.name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(archive.extractfile(member).read());checked(target,pins['source'][member.name])
    source_check(dest/'src',pins['source'])
    print(json.dumps(dict(output=str(dest),files=len(pins['source']),expanded_bytes=total,step=400)))

if __name__=='__main__':
    try:raise SystemExit(main())
    except (Refusal,OSError,ValueError) as e:print('REFUSED: '+str(e),file=sys.stderr);raise SystemExit(2)
