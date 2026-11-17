"""Authenticate an operator-fetched return before local extraction."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.item_ids import decode_inventories
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'kit/launcher'))
import orchard_results as R
import orchard_stage as S

def unpack(destination):
    root=Path(destination);config=json.loads((root/'CONFIG.json').read_text())
    receipt=json.loads((root/'fetched/EXIT.json').read_text())
    submission=json.loads((root/'SUBMISSION.json').read_text())
    if (submission.get('status')!='SUBMITTED' or receipt.get('token')!=config['token']
            or str(receipt.get('job'))!=str(submission['job'])):
        raise ValueError('Return job identity differs')
    archive=root/'fetched/result.tar.gz'
    R.verify(receipt,archive,config['plan_sha256'])
    target=root/'fetched/x';target.mkdir()
    with archive.open('rb') as stream:S.extract_stream(stream,target,None,512*1024**2)
    decode_inventories(target)
    return target

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--destination',required=True)
    print(unpack(p.parse_args().destination))
