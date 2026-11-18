# Replays row_removals.row_keys (cp/work/tree/student_pilot/row_removals.py:9-15) over every v7 row; counts matches vs B1 and n.json by family
import sqlite3,json,collections
def row_keys(row):
    values=[row.get("row_key"),row.get("qid")]
    for f in ("pointing","grounding","provenance"):
        if isinstance(row.get(f),dict): values.append(row[f].get("row_key"))
    values.extend(row.get("label_row_keys",[]))
    return {str(v) for v in values if v is not None}
B1={json.loads(l)['row_key'] for l in open('/scratch/jjyeung/orch_n30/r1_ops6/cf/final_evidence/COUNT_FIX_REMOVE_B1.jsonl')}
N={json.loads(l)['row_key'] for l in open('/scratch/jjyeung/orch_n30/r1_ops6/snapm/snap_9dd2fbb7/out/records/n.json')}
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?immutable=1&mode=ro',uri=True)
mb=collections.Counter(); mn=collections.Counter(); multi=0; extra=collections.Counter(); hitB=set()
for i,r,t in c.execute("select i,row,target from rows"):
    d=json.loads(r); k=row_keys(d)
    if len(k)>1: extra[d['question_type']]+=1
    if k&B1: mb[d['question_type']]+=1; hitB|=k&B1
    if k&N: mn[d['question_type']]+=1
    if (k&B1) and (k&N): multi+=1
res=dict(B1_matched_rows_by_type=mb,n_matched_rows_by_type=mn,both=multi,rows_with_extra_keys_by_type=extra,B1_keys_hit=len(hitB))
print(json.dumps(res)); json.dump(res,open('../out/KEYMATCH.json','w'),indent=1)
