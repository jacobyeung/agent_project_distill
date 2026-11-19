"""Run the reviewer's majority-per-feature clause classifier on D7 and its controls."""
import ast,collections as C,hashlib,json,re,sqlite3
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'out';DB=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
def pin(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return dict(sha256=h.hexdigest(),bytes=p.stat().st_size)
def reviewer_functions(name,wanted,env):
 p=B/'reference/reviewer'/name;tree=ast.parse(p.read_text())
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted]
 assert len(nodes)==len(wanted);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),env);return env
bayes=reviewer_functions('rev_balance.py',{'bayes'},{'C':C})['bayes']
census=reviewer_functions('rev_census.py',{'clause','opening'},{'re':re})
# This exact expression is the reviewer's mask in rev_balance.main.
MASK=r'\b(facing away from|turned away from|with my back to|face away from|face toward|facing toward|facing|looking at|looking toward|look toward|toward|face|ahead)\b'
assert MASK in (B/'reference/reviewer/rev_balance.py').read_text()
def masked(q,names):
 for n in sorted(set(names),key=len,reverse=True):q=q.replace(n,'<N>')
 return re.sub(MASK,'<C>',q)
rows=[json.loads(x) for x in (O/'NEW_ROWS.jsonl').read_text().splitlines()]
maps=[json.loads(x) for x in (O/'SOURCE_MAP.jsonl').read_text().splitlines()]
con=sqlite3.connect(DB.as_uri()+'?mode=ro&immutable=1',uri=True)
teach=[];pair_mismatches=[];source_rows=[]
for r,m in zip(rows,maps,strict=True):
 raw=con.execute('select row from rows where i=?',(m['source_i'],)).fetchone()[0];s=json.loads(raw);source_rows.append(s)
 assert hashlib.sha256(raw.encode()).hexdigest()==m['source_row_sha256']
 for row,new in ((s,False),(r,True)):
  q=row['student_input']['question'];ns=tuple(m['objects'])
  teach.append(dict(cl=census['clause'](q),op=census['opening'](row['target']),masked=masked(q,ns),
   names=tuple(sorted(set(ns))),roles=ns,dataset=row['dataset'],frames=tuple(row['student_input']['frame_indices']),
   options=tuple(row['student_input']['options']),new=new))
 a,b=teach[-2:]
 if (a['masked'],a['op'],a['names'])!=(b['masked'],b['op'],b['names']):pair_mismatches.append(r['qid'])
 assert (a['cl'],b['cl'])==('toward','away')
features={
 'opening':lambda t:t['op'], 'masked_question_wording':lambda t:t['masked'].split('\n')[0],
 'full_masked_question_wording':lambda t:t['masked'], 'name_set':lambda t:t['names'],
 'masked_question+opening+name_set':lambda t:(t['masked'],t['op'],t['names']),
 'masked_question+opening+role_triple+dataset+frame_indices+option_order':lambda t:(t['masked'],t['op'],t['roles'],t['dataset'],t['frames'],t['options']),
 'reviewer_new_template+name_set':lambda t:(t['masked'].startswith('At the <N>'),t['names'])}
acc={k:dict(zip(('accuracy','feature_values'),bayes(teach,f))) for k,f in features.items()}
assert not pair_mismatches and max(v['accuracy'] for v in acc.values())==0.5
survey=json.loads((O/'SURVEY.json').read_text())
def mix(pop):
 c=C.Counter()
 for r in pop:
  if r['opening']=='Step 1':c[r['clause']]+=r['rows']
 return dict(c)
all_before=mix(survey['before']);admitted_before=mix(survey['admitted'])
all_after=dict(all_before);all_after['away']=all_after.get('away',0)+len(rows)
admitted_after=dict(admitted_before);admitted_after['away']=admitted_after.get('away',0)+len(rows)
# Seen already has toward/away wording twins; count exact masked question/name/scene keys.
seen=C.defaultdict(C.Counter);byqid={m['qid']:m for m in survey['rows']};seen_rows=C.Counter()
for i,raw in con.execute('select i,row from rows'):
 r=json.loads(raw);meta=byqid.get(r['qid'])
 if not meta or meta['refused'] or meta['opening']!='Seen' or meta['family']=='medium':continue
 cl=census['clause'](r['student_input']['question']);seen_rows[cl]+=1
 if cl in ('toward','away'):
  key=(masked(r['student_input']['question'],meta['objects']),tuple(meta['objects']),r['dataset'],r['scene'],tuple(r['student_input']['frame_indices']))
  seen[key][cl]+=1
seen_paired=sum(min(c['toward'],c['away']) for c in seen.values())
pins={str(p):pin(p) for p in [Path(__file__),B/'reference/reviewer/rev_balance.py',B/'reference/reviewer/rev_census.py',O/'NEW_ROWS.jsonl',O/'SOURCE_MAP.jsonl',O/'SURVEY.json',DB]}
v=dict(command='nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 python leak_test.py',input_sha256=pins,
 status='PASS',teaching_rows=len(teach),threshold=0.60,best_clause_accuracy=max(x['accuracy'] for x in acc.values()),
 clause_bayes_accuracy=acc,method='Exact reviewer rev_balance.bayes majority class per feature value; exact reviewer clause mask; full-question joint feature adds opening and exact name set.',
 pair_feature_mismatches=pair_mismatches,opening_clause=dict(C.Counter(f"{t['op']}|{t['cl']}" for t in teach)),
 Step1_wording_clause_mix=dict(v7_before=all_before,v7_plus_new_after=all_after,admitted_before=admitted_before,admitted_after=admitted_after,teaching_subset={'toward':8000,'away':8000}),
 Seen=dict(existing_admitted_easy_hard_clauses=dict(seen_rows),exact_masked_wording_source_pairs=seen_paired,new_rows=0,reason='Existing Seen sources already include away wording; all 8,000 new rows target the toward-only Step-1 family.'),
 limitation='Chance-level guarantee applies to the paired teaching subset and these clause-masked features. Full v7 remains imbalanced; answers and traces contain the intended direction signal.')
(O/'LEAK_TEST.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
(B/'STATUS.md').write_text('The leak test passes: the reviewer’s best classifier on full clause-masked wording, opening and exact name set scores 50% across 16,000 source-plus-twin rows. Every pair has identical masked wording. Room-path verification and final semantic review are recorded separately.\n')
print(json.dumps({k:v for k,v in v.items() if k not in ('input_sha256',)},indent=1))
