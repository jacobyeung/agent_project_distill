"""Verify a fetched result against the prepared plan and unpack only safe members."""
from pathlib import Path
import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from guard_core import read,write,digest
from transport import verify_return,extract
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for name in ('config','receipt','archive','out'):p.add_argument('--'+name,required=True)
 a=p.parse_args();cfg=read(a.config);receipt=read(a.receipt)
 if cfg['plan_sha256']!=digest({k:v for k,v in cfg.items() if k!='plan_sha256'}):raise ValueError('Prepared plan seal differs')
 verify_return(receipt,a.archive,cfg['plan_sha256'])
 extract(a.archive,Path(a.out),300_000_000)
 write(Path(a.out)/'FETCH_VERIFIED.json',dict(status='PASS',plan_sha256=cfg['plan_sha256'],archive=receipt['archive']))
