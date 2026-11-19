from common import *
import subprocess,collections,ast
R=Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/A/src')
roots=[TREE,W/'fixtures',R]
files=subprocess.check_output(['rg','-l','--glob','*.json','--glob','*.jsonl','"question"\\s*:',*map(str,roots)],text=True).splitlines()
questions=set();rel=set();fail=[];counts={}
def walk(x):
 n=0
 if isinstance(x,dict):
  if isinstance(x.get('question'),str):
   questions.add(x['question']);n+=1
   if x.get('question_type',x.get('type'))=='relative_count':rel.add(x['question'])
  for v in x.values():
   if isinstance(v,(dict,list)):n+=walk(v)
 elif isinstance(x,list):
  for v in x:
   if isinstance(v,(dict,list)):n+=walk(v)
 return n
for name in files:
 p=Path(name)
 if p.stat().st_size>512*1024*1024:fail.append({'path':name,'reason':'over 512 MiB; not parsed'});continue
 try:
  n=0
  if p.suffix=='.jsonl':
   for l in p.open():
    if l.strip():n+=walk(json.loads(l))
  else:n=walk(json.loads(p.read_text()))
  if n:pin(p);counts[name]=n
 except (ValueError,RecursionError) as e:fail.append({'path':name,'reason':str(e)[:100]})
# Literal question templates in kit Python are also comparison references.
for root in [TREE,R/'tree']:
 for p in root.rglob('*.py'):
  if p.stat().st_size>2*1024*1024:continue
  try:t=ast.parse(p.read_text())
  except (SyntaxError,UnicodeError):continue
  strings={n.value for n in ast.walk(t) if isinstance(n,ast.Constant) and isinstance(n.value,str) and '?' in n.value and 12<=len(n.value)<=600 and '\n' not in n.value}
  if strings:questions.update(strings);pin(p)
out=dict(input_sha256=PINS,questions=sorted(questions),relative_count_wordings=sorted(rel),file_question_counts=counts,skipped=fail,discovery_roots=list(map(str,roots)),candidate_files=len(files))
dump(ROOT/'in/WORDING_CORPUS.json',out)
print(json.dumps(dict(unique=len(questions),relative=len(rel),files=len(counts),skipped=fail)))
