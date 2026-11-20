"""Join authenticated complete primary records, including killed gzip streams."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gpkg.capture_io import Records
from gpkg.join_v2 import join


def score(capture,receipt,gt,out,upload_receipt=None):
    receipt=json.loads(Path(receipt).read_text())
    if type(receipt.get('trusted')) is not bool:raise ValueError('missing parity flag')
    records=Records(capture,upload_receipt or receipt)
    truth=json.loads(Path(gt).read_text())
    flags={r['item_id']:r for r in receipt.get('per_item',[])}
    seen=set()
    with Path(out).open('x') as dest:
        for row in records:
            if row['pass_index']==1:continue
            if row['pass_index']!=0 or row['item_id'] in seen:raise ValueError('duplicate or invalid primary record')
            seen.add(row['item_id'])
            annotation=truth.get(row['item_id'],truth.get(row['capture']))
            if not row['objects']:
                values=[dict(key=row['item_id'],stage='U',reason='no recorded object call')]
            elif annotation is None:
                values=[dict(key=row['item_id']+':'+o['name'],stage='U',reason='missing GT file') for o in row['objects']]
            else:values=join(row,annotation)
            for value in values:
                value.update(trusted=receipt['trusted'],discrete_match=flags.get(row['item_id'],{}).get('discrete_match'))
                dest.write(json.dumps(value,allow_nan=False)+'\n')
    report=dict(records.report,primary_records=len(seen))
    report['receipt_counts_match']=(len(seen)==receipt.get('items') and records.report['records']==receipt.get('capture_records'))
    Path(str(out)+'.receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    if not report['salvaged'] and 'capture_records' in receipt and not report['receipt_counts_match']:
        raise ValueError('capture record count differs')
    print(json.dumps(report))
    return report


def main():
    p=argparse.ArgumentParser()
    for key in ('capture','receipt','gt','out'):p.add_argument('--'+key,required=True)
    p.add_argument('--upload-receipt')
    a=p.parse_args();score(a.capture,a.receipt,a.gt,a.out,a.upload_receipt)


if __name__=='__main__':main()
