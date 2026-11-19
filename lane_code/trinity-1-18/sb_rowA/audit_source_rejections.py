"""Distinguish numeric representation refusals from printed-response mismatches."""
from camera_contract import *
import re
from decimal import Decimal
pin(__file__);pin(ROOT/'camera_contract.py');pin(SRC)
t=load(OUT/'TRAINING_CHECKS.json')
keys={re.search(r"\('([^']+)'",s)[1] for s in t['source_rejections']}
records=[]
for line in gzip.open(SRC,'rt'):
 e=json.loads(line);r=json.loads(e['row'])
 if r['qid'] not in keys:continue
 raw=r['routing'];resp=next(x['text'] for x in raw['events'] if x['kind']=='tool_response')
 try:geometry(r)
 except AssertionError as exc:why=exc.args[0]
 else:raise AssertionError('Expected rejection disappeared')
 rec=dict(qid=r['qid'],type=raw['question_type'],answer=raw['answer'],gt_answer=raw['gt_answer'],response=resp,source_row_sha256=hashlib.sha256(e['row'].encode()).hexdigest(),reason=why)
 if raw['question_type']=='camera_displacement':
  value=re.search(r'distance = ([0-9.]+) m',resp)[1]
  rec['numerically_equal']=Decimal(raw['answer'])==Decimal(raw['gt_answer'])==Decimal(value)
  rec['classification']='numeric_string_representation' if rec['numerically_equal'] else 'numeric_value'
 else:rec['classification']='printed_response_recomputation'
 records.append(rec)
assert len(records)==14
counts=Counter(r['classification'] for r in records)
assert counts=={'numeric_string_representation':13,'printed_response_recomputation':1}
save(OUT/'SOURCE_REJECTIONS.json',dict(status='PASS',command='/scratch/jjyeung/envs/p1cpu/bin/python -B audit_source_rejections.py',counts=counts,rows=records))
print(enc(counts))
