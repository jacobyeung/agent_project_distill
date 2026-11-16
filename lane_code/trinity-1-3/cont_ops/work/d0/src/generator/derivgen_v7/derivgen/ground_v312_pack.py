"""Package reviewed grounding suffixes with exact teacher-forced loss masks."""
import argparse
import json
from pathlib import Path

from .ground_v312 import validate_evidence
from .ground_v312_io import sha
from .trace import loss_spans
from .ground_v312_quality import selection_refusal


def training_row(row):
    if row.get('spec_version') == '3.13':
        refusal = selection_refusal(row)
        if refusal:
            raise ValueError(refusal)
        if row.get('gt_accepted') is False:
            raise ValueError('row excluded from candidate selection')
        from .ground_v313_pack import training_row as pack_box
        return pack_box(row)
    if row.get('spec_version') != '3.12.2':
        raise ValueError('requires rendered revision 3.12.2; migrate old responses before packing')
    refusal = selection_refusal(row)
    if refusal:
        raise ValueError(refusal)
    if row.get('gt_accepted') is False:
        raise ValueError('row excluded from candidate selection')
    validate_evidence(row)
    if not row['gt_agrees'] or row['suffix_tokens']>5000:
        raise ValueError('row is not GT/cap admitted')
    target=row['suffix'];cursor=0;spans=[]
    for i,event in enumerate(row['events']):
        block=event['call']+'\n'+event['response']
        begin=target.index(block,cursor)+len(event['call'])+1
        end=begin+len(event['response']);cursor=end
        spans.append(dict(start=begin,end=end,role='tool',target_loss=0,
                          event_index=i,event_id=f'event-{i}',call_id=f'ground-{i}'))
    return dict(row,target=target,question_type=row['type'],
                form='spec-v3.12-ground-v1',trace_revision='3.12.2',
                tool_output_spans=spans,loss_spans=loss_spans(target,spans),
                schema='ground-routing-review-row-v1',training_admitted=False)


def pack(build,output):
    build,output=Path(build),Path(output)
    output.mkdir(parents=True,exist_ok=False)
    counts={}
    for source,name in [('balanced','balanced_training_rows'),('gt_accepted','gt_accepted_training_rows')]:
        n=0
        with (build/(source+'.jsonl')).open() as f,(output/(name+'.jsonl')).open('x') as out:
            for line in f:
                row=training_row(json.loads(line));out.write(json.dumps(row,allow_nan=False)+'\n');n+=1
        counts[name]=n
    receipt=dict(status='REVIEW-ONLY; consumer form/revision admission still required',counts=counts,
                 build_receipt_sha256=sha(build/'RECEIPT.json'),pack_module_sha256=sha(__file__),
                 tool_spans='half-open Unicode character offsets; forced tool responses have loss zero',
                 outputs={p.name:sha(p) for p in output.glob('*.jsonl')})
    (output/'PACK_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--build',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();print(json.dumps(pack(args.build,args.output)))


if __name__=='__main__':main()
