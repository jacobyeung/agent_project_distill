import json,re,collections,hashlib
E='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_r1anon7/ANON_SCAN_R1C4.json'
d=json.load(open(E))
S='/scratch/jjyeung/orch_n30/r1_ops6/work/xfer/scan1.out'
lines=open(S).read().split('\n')
if lines[-1]=='':lines.pop()
op=re.compile(r'split|revsi|vsibench|vsi|distill|qgen|scannet|arkit|qwen|sft|student|benchmark|eval',re.I)
pre=re.compile(r"(?i)scannet(pp)?|arkit\w*|scene\d{4}|vsi[-_ ]?bench|vsti?bench|dsibench|\bvsi\b|revsi|qwen[\w.-]*|\bsplit\b|distill\w*|\bqgen\b|gemini|/scratch/jjyeung|/home/jjyeung|orch_n\d+|agent_project\w*|\bteacher\b|\bstudent\w*|spatial|benchmark\w*|hypersim|multiscan|scanqa|sqa3d|\bvqa\b")
heads={'NEW / BUNDLE NAMES AND SUBMISSION ARGV':'NEW','INHERITED NAMES INSIDE VERIFIED 0700 TREES / INHERITED STAGING LOCATORS':'INHERITED','SEALED SCRIPT COMMAND LINES FOR ARGV REVIEW (NO SESSION CONTENTS)':'COMMANDS','GREP NEW NAMES':'GREP_NEW','GREP INHERITED NAMES / ARGV (account for each under the ruling)':'GREP_INHERITED'}
norm=lambda t:t.replace('7f1589c1','ee227714').replace('05b8ac69','6ed2c7aa')
c4={}
for h in d['hits']:
  k=(h['section'],norm(h['text']))
  c4.setdefault(k,h)
c4text={}
for h in d['hits']: c4text.setdefault(norm(h['text']),h)
sec=None;hits=[];unm=[];dup=0;seen={}
for i,l in enumerate(lines,1):
  if l in heads: sec=heads[l];continue
  if l.startswith(('PACKET ','MANIFEST ','PENDING ')): sec='TAIL';continue
  m=sorted(set(x.group(0) for x in op.finditer(l))|set(x.group(0) for x in pre.finditer(l)))
  if not m: continue
  key=(sec,l)
  if key in seen: dup+=1;continue
  seen[key]=i
  p=c4.get(key) or c4text.get(l)
  if p: hits.append((i,sec,l,m,p))
  else: unm.append((i,sec,l,m))
print('hits matched',len(hits),'unmatched',len(unm),'dup',dup)
print(collections.Counter((p['class'],s) for i,s,l,m,p in hits))
for u in unm: print('UNM',u[0],u[1],u[2][:300],u[3])
# C4 classified hits not found in C'
found={(p['section'],norm(p['text'])) for *_,p in hits}
miss=[h for h in d['hits'] if (h['section'],norm(h['text'])) not in found]
print('C4 hits not present',len(miss))
for h in miss[:40]: print('MISS',h['line'],h['section'],h['text'][:250])
