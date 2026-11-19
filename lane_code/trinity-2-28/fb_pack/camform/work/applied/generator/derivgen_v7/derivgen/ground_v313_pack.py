"""Successor review packaging with exact forced-response loss masks."""
from .ground_v312 import validate_evidence
from .trace import loss_spans


def training_row(row):
    from .ground_v312_quality import selection_refusal
    refusal = selection_refusal(row)
    if refusal:
        raise ValueError(refusal)
    if row.get('gt_accepted') is False:
        raise ValueError('row excluded from candidate selection')
    if row.get('spec_version')!='3.13' or not row.get('gt_agrees') or row['suffix_tokens']>5000:
        raise ValueError('requires GT-agreeing bounded v3.13 row')
    validate_evidence(row)
    if any('mode="box"' in e['call'] for e in row['events']):
        from .box_v313 import replay_audit
        replay_audit(row['events'])
    target=row['suffix'];cursor=0;spans=[]
    for i,event in enumerate(row['events']):
        block=event['call']+'\n'+event['response']
        begin=target.index(block,cursor)+len(event['call'])+1
        end=begin+len(event['response']);cursor=end
        spans.append(dict(start=begin,end=end,role='tool',target_loss=0,
                          event_index=i,event_id=f'event-{i}',call_id=f'ground-{i}'))
    return dict(row,target=target,question_type=row['type'],form='spec-v3.13-ground-v1',trace_revision='3.13',
                tool_output_spans=spans,loss_spans=loss_spans(target,spans),
                schema='ground-routing-review-row-v1',training_admitted=False)
