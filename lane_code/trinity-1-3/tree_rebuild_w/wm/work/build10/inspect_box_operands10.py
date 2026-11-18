from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];N=L;B=L/'work/build10';out=[]
for name in ('a0_pool_abs_distance_reworded.jsonl','a0_recovery.jsonl','a0_room.jsonl'):
    path=N/'work/rows_slices/slices_final'/name
    with path.open() as f:row=json.loads(next(f))
    source=row.get('ground_record') or row;audit=source.get('program_audit',{})
    record=dict(source=str(path),audit_keys=sorted(audit),boxes=audit.get('independent_ordered_boxes'),
        events=[v for v in source.get('events',[]) if v.get('kind')=='tool_response'][:2])
    out.append(record)
(L/'work/merge11/proofs/parity/BOX_OPERAND_EXAMPLES.json').write_text(json.dumps(out,indent=2)+'\n')
for r in out:print(json.dumps(r)[:2400])
