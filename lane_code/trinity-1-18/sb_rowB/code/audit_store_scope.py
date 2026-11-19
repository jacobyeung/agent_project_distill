import json,re,sqlite3
from collections import Counter,defaultdict
from inventory import ROOT,STORE,sha,FAMILIES
p=STORE/'vqa/rows.sqlite';c=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True)
counts=Counter();examples=defaultdict(list);total=0
for raw, in c.execute('select row from rows order by i'):
 r=json.loads(raw);total+=1;q=r.get('question') or r.get('student_input',{}).get('question','')
 if re.search(r'camera',q,re.I) and re.search(r'frame|time',q,re.I) and re.search(r'closest|nearest|furthest|farthest|distance|near/far',q,re.I):
  f=r.get('question_type',r.get('category'));counts[f]+=1
  if len(examples[f])<5:examples[f].append(dict(qid=r['qid'],question=q))
assert total==204413
out=dict(input_sha256={str(p):sha(p),str(ROOT/'code/audit_store_scope.py'):sha(ROOT/'code/audit_store_scope.py')},scanned_rows=total,query='camera AND (frame OR time) AND (closest OR nearest OR furthest OR farthest OR distance OR near/far), case-insensitive',family_counts=dict(counts),outside_selected_families={k:v for k,v in counts.items() if k not in FAMILIES},examples=dict(examples))
(ROOT/'out/STORE_SCOPE.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(total=total,counts=counts,outside=out['outside_selected_families']),indent=2))
