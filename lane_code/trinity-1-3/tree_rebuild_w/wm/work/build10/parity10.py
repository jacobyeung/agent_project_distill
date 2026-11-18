"""Count immutable bound responses; missing numerical inputs never count as parity."""
from pathlib import Path
from collections import Counter
import hashlib,itertools,json,re
L=Path(__file__).resolve().parents[2];N=L;B=L/'work/build10';out=L/'work/merge11/proofs/parity'
out.mkdir(parents=True,exist_ok=True)
families=[]
for path in sorted((N/'work/rows_slices').rglob('*.jsonl')):
    counts=Counter();h=hashlib.sha256();examples=[];rows=0;has_raw=0;has_independent_boxes=0
    with path.open('rb') as source:
        for raw in itertools.islice(source,2000):
            h.update(raw);row=json.loads(raw);rows+=1
            text=row.get('target',row.get('suffix',''))
            pairs=re.findall(r'(<(?:pose|turn|move|depth_at|ground|gap)\b[^>]*>).*?<tool_response>(.*?)</tool_response>',text,re.S)
            for call,response in pairs:
                kind=re.match(r'<(\w+)',call)[1]
                counts[kind]+=1
                if len(examples)<10:examples.append(dict(qid=row.get('qid'),kind=kind,
                    response_sha256=hashlib.sha256(response.encode()).hexdigest()))
            if any(k in row for k in ('pose9','raw_pose','depth_map','heads','head_inputs')):has_raw+=1
            producer=row.get('ground_record') or row
            if producer.get('program_audit',{}).get('independent_ordered_boxes'):has_independent_boxes+=1
        extra=next(source,None) is not None
    families.append(dict(source=str(path),rows=rows,more_than_slice_limit=extra,slice_sha256=h.hexdigest(),
        raw_head_inputs_present=has_raw,independent_box_audit_rows=has_independent_boxes,response_kinds={k:dict(bound=n,checked=0,identical=0,different=0,
            blocked=n,missing_input=('exact producer camera/reference transform and provider geometry; independent world-box audits do not supply the original serving operands'
                if k in ('ground','gap') else 'raw producer pose rotations / depth maps / FoV and exact reader inputs'))
            for k,n in sorted(counts.items())},examples=examples))
value=dict(status='BLOCKED_BOUND_RAW_INPUTS',families=families,
    note='Some rows retain independent world-box audits. They do not supply the original producer camera/reference transform, depth, or provider-selection inputs. Printed responses cannot supply those missing operands. No response was relabelled identical by comparing it with itself. Source rows were read in place and not changed.',
    build7_inventory=str(L/'work/merge11/proofs/parity_build7/RESULT.json'))
(out/'BYTE_PARITY.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(dict(families=len(families),rows=sum(r['rows'] for r in families),raw_inputs=sum(r['raw_head_inputs_present'] for r in families))))
