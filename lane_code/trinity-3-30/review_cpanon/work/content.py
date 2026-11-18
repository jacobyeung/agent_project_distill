import re,json,collections
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/r1_ops6/work')
op=re.compile(r'split|revsi|vsibench|vsi|distill|qgen|scannet|arkit|qwen|sft|student|benchmark|eval',re.I)
pre=re.compile(r"(?i)scannet(pp)?|arkit\w*|scene\d{4}|vsi[-_ ]?bench|vsti?bench|dsibench|\bvsi\b|revsi|qwen[\w.-]*|\bsplit\b|distill\w*|\bqgen\b|gemini|/scratch/jjyeung|/home/jjyeung|orch_n\d+|agent_project\w*|\bteacher\b|\bstudent\w*|spatial|benchmark\w*|hypersim|multiscan|scanqa|sqa3d|\bvqa\b")
extra=re.compile(r'(?i)/home/[a-z]|cprime|c_prime|\bproject\b|okh7|jjyeung|jyeung|count_diag|first_seen|counting|totals')
pairs=[('BINDING.json','BINDING.json'),('config.json','config.json'),('c4.json',None),('e.txt','e.txt'),('ids.json','ids.json'),('jb.sh','jb.sh'),('p_05b8ac69.sh','p_6ed2c7aa.sh'),(None,'z.json'),('s.sh','s.sh'),('sums.txt','sums.txt')]
def hits(p,rx):
  c=collections.Counter()
  if p is None or not p.exists(): return c
  for l in p.read_text(errors='replace').splitlines():
    for m in rx.finditer(l): c[m.group(0).lower()]+=1
  return c
out={}
for a,b in pairs:
  pa=W/'ex_08f3a7b2'/a if a else None; pb=W/'ex_32337655'/(b or a)
  r={}
  for nm,rx in (('op',op),('pre',pre),('extra',extra)):
    ca,cb=hits(pa,rx),hits(pb,rx)
    r[nm]={'c4':dict(ca),'cp':dict(cb),'new_or_more':{k:v for k,v in cb.items() if v>ca.get(k,0)}}
  out[b or a]=r
  print(b or a, {nm:r[nm]['new_or_more'] for nm in r})
json.dump(out,open('content_regex.json','w'),indent=1)
# z.json structure
z=json.load(open(W/'ex_32337655/z.json'))
print(type(z), (list(z.keys()) if isinstance(z,dict) else len(z)))
