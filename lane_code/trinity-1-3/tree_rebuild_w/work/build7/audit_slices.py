"""Bounded row, response and aspect-ratio audit. Never changes source rows."""
import collections,hashlib,json,re,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';P=L/'work/build7/proofs/rows'
P.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(T))
from student_pilot.r0_exclusion import reserve
from student_pilot.row_text_audit import reasons,PATTERNS,SOURCES
from student_pilot.response_spec import check
from student_pilot import ground_rows
records=[]
paths=sorted((L/'work/rows_slices/slices_final').glob('*.jsonl'))
paths+=sorted((L/'fixtures/rows/slices_v3').glob('*.jsonl'))
for path in paths:
 counts=collections.Counter();examples=[];h=hashlib.sha256();forms=collections.Counter();dimensions=collections.Counter()
 for index,raw in enumerate(path.open('rb')):
  if index>=2000:break
  h.update(raw);row=json.loads(raw);counts['rows']+=1
  hits=reserve().matches(row)
  if hits:counts['r0_refused']+=1
  rules=reasons(row)
  for rule in rules:counts[rule]+=1
  text=row.get('target',row.get('suffix',''));responses=re.findall(r'<tool_response>.*?</tool_response>',text,re.S)
  forms[row.get('answer_form','routed' if responses else 'direct')]+=1
  errors=[]
  for response in responses:
   counts['responses']+=1
   try:check(response);counts['response_roundtrip']+=1
   except (ValueError,TypeError,KeyError,AssertionError) as e:
    counts['response_spec_refused']+=1;errors.append(str(e))
  # Execute the real producer and reader when its source record is supplied.
  if row.get('ground_record'):
   try:
    produced=ground_rows.pack(dict(row['ground_record'],suffix=text),row.get('provenance',{}))
    ground_rows.validate(produced);counts['producer_reader_pass']+=1
   except (ValueError,TypeError,KeyError,AssertionError) as e:
    counts['producer_reader_refused']+=1;errors.append(str(e))
  for f in row.get('student_input',{}).get('frames',[]):
   if not isinstance(f,dict):dimensions['unknown']+=1;continue
   height,width=f.get('height'),f.get('width')
   if isinstance(height,int) and isinstance(width,int):dimensions['portrait' if height>width else 'landscape_or_square']+=1
   else:dimensions['unknown']+=1
  if len(examples)<200:examples.append(dict(qid=row.get('qid'),row_sha256=hashlib.sha256(raw).hexdigest(),r0=hits,rules=rules,errors=errors))
 record=dict(source=str(path.relative_to(L)),slice_sha256=h.hexdigest(),counts=dict(counts),answer_forms=dict(forms),
             frame_dimensions=dict(dimensions),full_store_checked=False,examples=examples)
 dest=P/(path.parent.name+'_'+path.stem+'.json');dest.write_text(json.dumps(record,indent=2)+'\n')
 records.append({k:v for k,v in record.items() if k!='examples'})
(P/'RESULTS.json').write_text(json.dumps(dict(families=records,patterns=PATTERNS,pattern_sources=SOURCES,
 limitation='Text signatures cannot establish that a numeric response came from an in-artifact head. Full stores, RGB dimensions and head provenance remain required.'),indent=2)+'\n')
print(json.dumps(dict(families=len(records),rows=sum(r['counts']['rows'] for r in records),
 responses=sum(r['counts'].get('responses',0) for r in records),
 response_refusals=sum(r['counts'].get('response_spec_refused',0) for r in records))))
