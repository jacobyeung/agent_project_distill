"""Extract an authenticated, completed result into a fresh local directory."""
import argparse
import json
from pathlib import Path
import sys
import tarfile
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'kit/launcher'))
import orchard_results as R


def extract(destination,output):
    destination=Path(destination);output=Path(output)
    cfg=json.loads((destination/'CONFIG.json').read_text())
    receipt=json.loads((destination/'fetched/EXIT.json').read_text())
    submission=json.loads((destination/'SUBMISSION.json').read_text())
    if receipt.get('token')!=cfg['token'] or receipt.get('job')!=submission['job']:
        raise ValueError('Returned identity differs')
    archive=destination/'fetched/result.tar.gz'
    R.verify(receipt,archive,cfg['plan_sha256'])
    output.mkdir(parents=True,exist_ok=False)
    with tarfile.open(archive) as stream:stream.extractall(output,filter='data')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--destination',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();extract(a.destination,a.output)
