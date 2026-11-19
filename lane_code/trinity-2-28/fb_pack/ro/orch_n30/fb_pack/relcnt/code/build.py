from common import *
import copy,sqlite3,collections
from student_pilot import trace_grammar

def main():
 source=load(BASE/'in/procedure_source.json')
 expected_store=(BASE/'in/INPUT_SHA256SUMS.txt').read_text().splitlines()[0].split()[0];pin(BASE/'in/INPUT_SHA256SUMS.txt')
 assert pin(STORE)['sha256']==expected_store
 db=sqlite3.connect(STORE.as_uri()+'?mode=ro&immutable=1',uri=True)
 found=db.execute('SELECT row FROM rows WHERE instr(row, ?) > 0',(source['qid'],)).fetchall();db.close()
 found=[(raw,) for raw, in found if json.loads(raw)['qid']==source['qid']]
 assert len(found)==1
 actual=json.loads(found[0][0]);assert actual==source and actual['question_type']=='object_counting'
 body=re.fullmatch(r'\nStep 1: (locate the distinct instances of box; count each once across the frames\.)\n',thought(actual)).group(1)
 procedure=body.replace('of box;','of {category};')
 seal=load(TREE.parent.parent/'out/TREE_SEAL.json')
 pin(BASE/'code/generate.py');pin(BASE/'code/wordings.py');pin(ROOT/'code/wordings.py');pin(SRC)
 selected=list(rows(BASE/'out/relative_count.jsonl'))
 identity(selected[0]);code_pins()
 inputs=dict(PINS)
 out=ROOT/'out/relative_count.jsonl'
 with out.open('w') as f:
  for src in selected:
   r=copy.deepcopy(src);m=r['provenance']['relative_count'];a,b=m['a'],m['b'];rel=m['relation']
   comparison=(f'So there are as many {a} instances as {b} instances.' if rel=='tie' else f'So there are {rel} {a} instances than {b} instances.')
   r['target']='<think>\n'+procedure.format(category=a)+'\n'+procedure.format(category=b)+'\n'+comparison+'\n</think>\n\n'+r['answer']
   assert not re.search(r'\d',thought(r))
   errors=trace_grammar.validate_row(r);assert not errors,(r['qid'],errors)
   r['provenance']['input_sha256'].update(inputs)
   assert identity(r)==r['candidate_id']
   f.write(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
 result=dict(status='BUILT',input_sha256=PINS,output=pin(out),rows=len(selected),tree_seal=seal,procedure_body=procedure,procedure_store_qid=source['qid'],step_labels='Omitted to keep the think block free of all numeric tokens.',allowed_changes=['target','provenance.input_sha256'],command='nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 python code/build.py')
 result['input_sha256']={k:v for k,v in PINS.items() if k!=str(out)}
 dump(ROOT/'out/BUILD.json',result)
 status('The packet contains 4,000 selected rows with two exact store counting-procedure bodies, one qualitative comparison in question order, and a final option letter. All 4,000 pass the w24 direct grammar with no digits in their think blocks. Questions, options, identifiers, sampling, frames, and GT annotations are preserved. Independent totals, balance, wording-distance, room, and review checks are pending.')
 print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'}))
if __name__=='__main__':main()
