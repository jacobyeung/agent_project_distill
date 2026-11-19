"""Reuse the reviewer's independent native, diff and signed-axis rules on all D7 rows."""
import ast,collections as C,hashlib,json,re,sqlite3,sys
from pathlib import Path
import cpu_native
from survey import d
from student_pilot import r2_contract,trace_grammar,r2_grammar
O=Path(__file__).resolve().parent/'out';B=O.parent
d.pin(d.DB,d.DB_SHA)
d.PINS.update(json.loads((O/'CHECKS.json').read_text())['input_sha256'])
p=B/'reference/reviewer/rev_verify.py';tree=ast.parse(p.read_text())
functions={'opts','body','native','pack_fn','diff'};constants={'HALF','PHRASE','QUAD'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in functions or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in n.targets)]
env=dict(re=re,ast=ast,TREE=d.TREE,r2_contract=r2_contract,trace_grammar=trace_grammar,r2_grammar=r2_grammar)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),env)
pack=env['pack_fn']();opts=env['opts'];body=env['body'];native=env['native'];diff=env['diff'];PHRASE=env['PHRASE'];QUAD=env['QUAD']
con=sqlite3.connect(d.DB.as_uri()+'?mode=ro&immutable=1',uri=True)
rows=[json.loads(l) for l in (O/'NEW_ROWS.jsonl').read_text().splitlines()];maps=[json.loads(l) for l in (O/'SOURCE_MAP.jsonl').read_text().splitlines()]
d6={json.loads(l)['provenance']['sb_rowD6']['source_qid']:json.loads(l) for l in (B/'work/d6_out/NEW_ROWS.jsonl').read_text().splitlines() if json.loads(l)['provenance']['sb_rowD6']['branch']=='a'}
phrases=C.Counter();diffs=C.Counter();overlap=0
for r,m in zip(rows,maps,strict=True):
 s=json.loads(con.execute('select row from rows where i=?',(m['source_i'],)).fetchone()[0]);X,Y,Z=m['objects'];sb,nb=body(s),body(r)
 line=sb[1]
 mm=(re.fullmatch(rf'Step 2: facing the {re.escape(Y)} from the {re.escape(X)}, I find the {re.escape(Z)} (.+)\.',line)
 or re.fullmatch(rf'Step 2: standing at the {re.escape(X)} and facing the {re.escape(Y)}, I find the {re.escape(Z)} (.+)\.',line)
 or re.fullmatch(rf'Step 2: I stand at the {re.escape(X)} facing the {re.escape(Y)}; I find the {re.escape(Z)} (.+)\.',line)
 or re.fullmatch(rf'Step 2: I find the {re.escape(Z)} (.+) when I stand at the {re.escape(X)} facing the {re.escape(Y)}\.',line))
 assert mm and mm[1] in PHRASE,(s['qid'],line)
 x,y=PHRASE[mm[1]];phrases[mm[1]]+=1
 assert QUAD[x,y]==opts(s)[s['answer']]
 assert QUAD[-x,-y]==opts(r)[r['answer']]==env['HALF'][opts(s)[s['answer']]]
 assert nb[1]==sb[1] and len(nb)==4 and 'Step 3: I face away from' in nb[2]
 changes=diff(s,r);diffs.update(changes)
 assert set(changes)<={'qid','pool','answer','target','facing','+facing','+candidate_id','+label_row_keys','student_input.question','+provenance.sb_rowD7'}
 native(s,pack);native(r,pack)
 if s['qid'] in d6:
  a=d6[s['qid']];overlap+=1
  for key in ('answer','target','scene','facing'):assert a[key]==r[key]
  assert {k:v for k,v in a['student_input'].items() if k!='question'}=={k:v for k,v in r['student_input'].items() if k!='question'}
for f in [Path(__file__),p,O/'NEW_ROWS.jsonl',O/'SOURCE_MAP.jsonl',B/'work/d6_out/NEW_ROWS.jsonl']:d.pin(f)
v=dict(command='nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 python reviewer_checks.py',input_sha256=d.PINS,status='PASS',
 rows=8000,native_rows_and_sources=16000,independent_signed_axis_truth=8000,phrases=dict(phrases),field_differences=dict(diffs),
 reused_reviewer_functions=sorted(functions),reused_reviewer_constants=sorted(constants),D6_away_source_overlap=overlap,D6_overlap_answers_traces_frames_options_identical=overlap)
(O/'REVIEWER_CHECKS.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in v.items() if k!='input_sha256'}))
