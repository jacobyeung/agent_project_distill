from common import *
seen=start('source_forms.py')
from student_pilot.trace_grammar import NUM
lineage={r['source_i']:r for r in rows(SBA/'out/CAMERA_LINEAGE.jsonl')};pin(SBA/'out/CAMERA_LINEAGE.jsonl')
admissions={r['i']:r for r in rows(SBA/'out/SOURCE_ADMISSION.jsonl')};pin(SBA/'out/SOURCE_ADMISSION.jsonl')
p=pin(SBA/'out/CAMERA_SOURCES.jsonl.gz');forms=Counter();reasons=Counter();types=Counter();variants=Counter();matched=Counter();examples={};qids=[];unique=set()
with gzip.open(p['path'],'rt') as f:
 for line in f:
  envelope=json.loads(line);idx=envelope['i'];raw=envelope['row'];r=json.loads(raw);q=r['qid'];typ=r['routing']['question_type'];types[typ]+=1
  h=hashlib.sha256(raw.encode()).hexdigest();lin=lineage[idx];ad=admissions[idx]
  assert h==lin['source_row_sha256']==ad['row_sha256'] and ad['keep'] and q==lin['source_qid']
  assert q not in unique;unique.add(q)
  fs=set()
  for e in r['routing']['events']:
   if e['kind'] not in ('plan','canonical_text'):continue
   name=form(e['text'])
   if name=='UNCLASSIFIED':continue
   fs.add(name);variants[NUM.sub('{number}',e['text'])]+=1
   text,ids=rewrite_text(e['text'])
   for rule in ids:matched[rule]+=1
   examples.setdefault(name,dict(qid=q,before=e['text'],after=text,rule_ids=ids))
  forms.update(fs)
  errors=shared_errors(r)
  if errors:reasons['Shared grammar: '+','.join(e.rule_id for e in errors)]+=1
  qids.append(dict(source_i=idx,source_qid=q,source_row_sha256=h,training_qid=lin['qid'],forms=sorted(fs),grammar_rules=[e.rule_id for e in errors]))
assert sum(types.values())==6000
classification=load(ROOT/'out/CLASSIFICATION.json');failure_variants=Counter()
for rec in classification['refusals']:
 for line in {e['line'] for e in rec['violations']}:failure_variants[NUM.sub('{number}',line)]+=1
capture(seen)
write('out/SOURCE_FORMS.json',dict(source=p,source_rows=len(unique),types=types,forms=forms,rewrite_rule_occurrences=matched,grammar_refusals=reasons,exact_numeric_normalized_variants=variants,wording_refusal_line_variants=failure_variants,examples=examples,records=qids,scope='The 6,000 authenticated camera source rows retained by sb_rowA, not an inventory of the unavailable full P routing base. Both offending forms occur here, so unchanged base source traces and rewritten camera wording traces would supply different prose forms for the same computation.'))
status(5,f'All {len(unique)} saved routing source rows match admission and lineage hashes. Both offending line forms occur in these P-source extracts. The complete P routing base is not local; its global counts are not claimed.')
print(dict(forms),dict(reasons),flush=True)
