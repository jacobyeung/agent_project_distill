from pathlib import Path
import difflib,dis,json,types
L=Path(__file__).resolve().parents[1];W=L/'work';trace={}
for tag in ('R6_FINAL_BASE','R6_FINAL_R1','R6_COVERAGE','R6_NEW'):
 p=W/f'{tag}_trace.json'
 if not p.exists():continue
 for rel,lines in json.loads(p.read_text()).items():
  for line,tests in lines.items():trace.setdefault(rel,{}).setdefault(line,set()).update(tag+': '+t for t in tests)
def executable(code):
 out={n for _,n in dis.findlinestarts(code) if n>0}
 for c in code.co_consts:
  if isinstance(c,types.CodeType):out.update(executable(c))
 return out
records=[];missing=[]
for before,after in [('src_r5','src_r6'),('tests_r5','tests_r6')]:
 for p in sorted((W/after).rglob('*.py')):
  rel=str(p.relative_to(W/after));prior=W/before/rel
  old=prior.read_text().splitlines() if prior.exists() else []
  source=p.read_text();new=source.splitlines();key=rel if after=='src_r6' else 'tests_r6/'+rel
  lines=executable(compile(source,str(p),'exec'))
  for op,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
   if op=='equal':continue
   for n in range(c+1,d+1):
    tests=sorted(trace.get(key,{}).get(str(n),set()))
    reason=None if tests else 'No executable instruction (comment, signature continuation, or literal).' if n not in lines else None
    record=dict(source=str(p),line=n,text=new[n-1],tests=tests,executed=bool(tests),reason=reason)
    records.append(record)
    if n in lines and not tests:missing.append(record)
   for n in range(a+1,b+1):
    records.append(dict(source=str(prior),line=n,text=old[n-1],tests=[],executed=False,reason='This side of the interdiff is absent from the r6 implementation.'))
(W/'coverage_detail_r6.json').write_text(json.dumps(dict(records=records,uncovered=missing),indent=2))
for r in missing:print(r['source'].split('/work/')[-1],r['line'],r['text'])
