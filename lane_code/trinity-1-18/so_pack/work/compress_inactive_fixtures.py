"""Losslessly encode named inactive fixtures; run only after user I/O approval."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import time

ROOT=Path('/scratch/jjyeung/orch_n30/so_pack')
NAMES=('tests01','tests02','tests03','tests04','tests05','tests06','tests07',
       'final_tests','release_tests','delivery_tests','verified_tests',
       'probe_guard','probe_guard2','probe_logic','probe_logic3','probe_logic4',
       'probe_metadata','probe_stop1','probe_stop2','probe_stop3','d_inventory_checks')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--approved',action='store_true');args=parser.parse_args()
    if not args.approved:raise SystemExit('User heavy-I/O approval is required')
    os.umask(0o077);start=time.monotonic();traffic=0;saved=0;count=0
    manifest=ROOT/'out/INACTIVE_FIXTURE_ENCODING.jsonl'
    if manifest.exists():raise SystemExit('Encoding already attempted; do not rerun')
    with manifest.open('x') as log:
        for name in NAMES:
            for parent,dirs,names in os.walk(str(ROOT/'work'/name)):
                dirs.sort()
                for filename in sorted(names):
                    path=Path(parent)/filename
                    if path.is_symlink() or path.stat().st_size<1024:continue
                    raw=path.read_bytes();traffic+=len(raw)
                    encoded=gzip.compress(raw,compresslevel=6,mtime=0)
                    if len(encoded)+512<len(raw):
                        row=dict(path=str(path.relative_to(ROOT)),codec='gzip',
                            bytes_original=len(raw),bytes_encoded=len(encoded),
                            sha256_original=hashlib.sha256(raw).hexdigest(),
                            sha256_encoded=hashlib.sha256(encoded).hexdigest(),
                            mode=path.stat().st_mode&0o777)
                        log.write(json.dumps(dict(row,state='prepared'))+'\n');log.flush()
                        path.write_bytes(encoded)
                        if gzip.decompress(path.read_bytes())!=raw:
                            raise RuntimeError('Lossless verification failed: '+str(path))
                        traffic+=3*len(encoded);saved+=len(raw)-len(encoded);count+=1
                        log.write(json.dumps(dict(row,state='verified'))+'\n');log.flush()
                    delay=traffic/8000000.0-(time.monotonic()-start)
                    if delay>0:time.sleep(min(delay,0.5))
            print('ENCODED',name,'files',count,'bytes_saved',saved,flush=True)
    print('LOSSLESS_ENCODING_PASS files='+str(count)+' bytes_saved='+str(saved),flush=True)


if __name__=='__main__':main()
