import json,re,hashlib,os
SCAN='/scratch/jjyeung/orch_n30/r1_ops/work/drv_p2/scan1.out'
EV='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_r1anon3'
EX='/scratch/jjyeung/orch_n30/r1_ops/work/ex_6f8ed106/'
BUN='/project/community/jjyeung/okh7/i_6f8ed106'
raw=open(SCAN,'rb').read();L=raw.decode().splitlines()
sha=lambda b:hashlib.sha256(b).hexdigest()
op=re.compile(r'split|revsi|vsibench|vsi|distill|qgen|scannet|arkit|qwen|sft|student|benchmark|eval',re.I)
pr=re.compile(r"(?i)scannet(pp)?|arkit\w*|scene\d{4}|vsi[-_ ]?bench|vsti?bench|dsibench|\bvsi\b|revsi|qwen[\w.-]*|\bsplit\b|distill\w*|\bqgen\b|gemini|/scratch/jjyeung|/home/jjyeung|orch_n\d+|agent_project\w*|\bteacher\b|\bstudent\w*|spatial|benchmark\w*|hypersim|multiscan|scanqa|sqa3d|\bvqa\b")
idx={h:i+1 for i,h in enumerate(L) if h in('NEW / BUNDLE NAMES AND SUBMISSION ARGV','INHERITED NAMES INSIDE VERIFIED 0700 TREES / INHERITED STAGING LOCATORS','SEALED SCRIPT COMMAND LINES FOR ARGV REVIEW (NO SESSION CONTENTS)','GREP NEW NAMES','GREP INHERITED NAMES / ARGV (account for each under the ruling)')}
n0,i0,c0,g0,h0=sorted(idx.values());end=[i+1 for i,l in enumerate(L) if l.startswith('PACKET ')][0]
def rng(a,b):return [(k,L[k-1]) for k in range(a+1,b)]
NEW=rng(n0,i0);INH=rng(i0,c0);CMD=rng(c0,g0);GN=rng(g0,h0);GI=rng(h0,end)
manifest=[l.split()[1] for l in L if l.startswith('MANIFEST ')][0]
tin={l.split(' :: ',1)[1] for _,l in INH if l.startswith(BUN+'/t.tar :: ')}
tnew={l.split(' :: ',1)[1] for _,l in NEW if l.startswith(BUN+'/t.tar :: ')}
dirs={'/'.join(m.split('/')[:i]) for m in tin|tnew for i in range(1,len(m.split('/')))}
inhdirs={'/'.join(m.split('/')[:i]) for m in tin for i in range(1,len(m.split('/')))}
qt=[(k,l) for k,l in NEW if l.startswith(BUN+'/qt')]
qtrel={l[len(BUN)+4:] for _,l in qt if l!=BUN+'/qt'}
assert qtrel==tin|tnew|dirs, 'qt tree differs from t.tar member set'
assert qtrel-dirs==tin|tnew
newline={l:k for k,l in NEW}
def m(s):return sorted(set(x.group(0) for x in op.finditer(s))|set(x.group(0) for x in pr.finditer(s)))
hits=[]
def add(k,sec,text,cls,why):hits.append(dict(file='drv_p2/scan1.out',line=k,section=sec,matches=m(text),text=text,cls=cls,why=why))
for k,l in GN:
  src=newline[l]
  if ' :: ' in l:
    add(k,'GREP_NEW',l,'exempt-content','new tar member name (same 3 members ruled exempt in proof 1, ANON_SCAN_R1P.json lines 2033-2038) inside t.tar / KH k/t_b83a8a35d420815b.tar in 0700 trees; also listed at NEW line %d'%src)
  else:
    rel=l[len(BUN)+4:]
    if rel in tin or rel in inhdirs:
      add(k,'GREP_NEW',l,'inherited-accepted','BUN/qt/ is the selector import tree q1.sh extracted from BUN/t.tar (sha-checked per member against c.json; mkdir 0o700, files 0600). "%s" is an inherited t.tar member/dir name (in H k/7.json, listed INHERITED); inherited name inside private 0700 tree: ORCH 1557Z item 1. NEW line %d'%(rel,src))
    else:
      add(k,'GREP_NEW',l,'exempt-content','BUN/qt/ extraction of a NEW t.tar member already ruled exempt in proof 1 (tar member name in 0700 tree); file name inside private 0700 BUN, not visible: ORCH 1557Z item 1 / 1758Z. NEW line %d'%src)
for k,l in GI:
  add(k,'GREP_INHERITED',l,'inherited-accepted','inherited KH runtime command line (b/c.sh, inherited section) ; same line accepted in proof 1' if '/b/c.sh:' in l else 'inherited name inside verified 0700 tree (H SHA256SUMS / H k/7.json); ORCH 1557Z item 1')
gset={l for _,l in GN}|{l for _,l in GI}
for sec,R in (('NEW',NEW),('INHERITED',INH),('COMMANDS',CMD)):
  for k,l in R:
    if l in gset or not pr.search(l):continue
    if sec=='COMMANDS':add(k,sec,l,'inherited-accepted','precedent-regex-only hit; inherited KH b/c.sh:351 bwrap argv token /home/jjyeung = account home, no forbidden word; identical to proof 1 scan line 1993 (inherited-accepted) and ORCH 1758Z N4 acceptance')
    elif sec=='INHERITED':add(k,sec,l,'inherited-accepted','precedent-regex-only ("spatial"); inherited t.tar member name in 0700 tree; ORCH 1557Z item 1')
    else:add(k,sec,l,'inherited-accepted','precedent-regex-only ("spatial"); BUN/qt/ extraction of inherited t.tar member tests/test_spatial_pose.py inside 0700 BUN; ORCH 1557Z item 1')
for h in hits:h['class']=h.pop('cls')
hits.sort(key=lambda h:h['line'])
from collections import Counter
cnt=Counter(h['class'] for h in hits)
ext=[]
for r,_,fs in os.walk(EX):
  for f in fs:
    p=os.path.join(r,f);rel=os.path.relpath(p,EX);ext.append(dict(path=BUN+'/'+rel,sha256=sha(open(p,'rb').read())))
ext.sort(key=lambda e:e['path'])
json.dump(dict(hits=hits,counts=dict(cnt),ext=ext,manifest=manifest,lines=len(L),sections=dict(new=[n0+1,i0-1],inh=[i0+1,c0-1],cmd=[c0+1,g0-1],grep_new=[g0+1,h0-1],grep_inh=[h0+1,end-1]),qt_counts=dict(entries=len(qt),inherited_members=len(tin),new_members=len(tnew),dirs=len(dirs))),open('cls.json','w'),indent=1)
print(cnt,len(hits),len(ext),manifest,len(qt))
print([h['line'] for h in hits if h['section'] in('NEW','INHERITED','COMMANDS')])
print([ (h['line'],h['text'][-50:]) for h in hits if h['section']=='GREP_NEW' and h['class']=='exempt-content'])
