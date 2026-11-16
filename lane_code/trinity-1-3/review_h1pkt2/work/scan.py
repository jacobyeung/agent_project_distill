import re,sys,json,os,tarfile,io,gzip
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/review_h1pkt2/work');H=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1')
PAT=re.compile(r'(?i)scannet(?:pp|\+\+)?|arkit\w*|\bscene\d{4}|vsi[-_ ]?bench|vsti?bench|dsibench|\bvsi\b|revsi|qwen[\w.\-]*|\bsplit\b|distill\w*|\bqgen\b|gemini|/scratch/jjyeung|/home/jjyeung|orch_n\d+|agent_project\w*|\bteacher\b|\bstudent\w*|spatial|benchmark\w*|hypersim|multiscan|scanqa|sqa3d|\bvqa\b')
def scan_bytes(label,name,data,out):
    if b'\0' in data[:4096]: 
        out.append(dict(surface=label,file=name,line=0,kind='binary',match=None,text='(binary)')) if PAT.search(data.decode('latin1')) else None; return
    t=data.decode('utf-8','replace')
    for i,l in enumerate(t.splitlines(),1):
        for m in PAT.finditer(l): out.append(dict(surface=label,file=name,line=i,match=m.group(0),text=l.strip()[:220]))
    for m in PAT.finditer(name): out.append(dict(surface=label,file=name,line=0,match=m.group(0),text='(member name)'))
hits=[]
pkg=W/'pkg'
for p in sorted(pkg.iterdir()):
    if p.suffix=='.tar':
        with tarfile.open(p) as tf:
            for m in tf:
                if m.isfile(): scan_bytes('trainer_tar',m.name,tf.extractfile(m).read(),hits)
                elif PAT.search(m.name): hits.append(dict(surface='trainer_tar',file=m.name,line=0,match=PAT.search(m.name).group(0),text='(dir name)'))
    else: scan_bytes('upload',p.name,p.read_bytes(),hits)
for n in ['orch_h1.sh','fin_h1.sh','build/g_patch.sh']: scan_bytes('transport',n,(H/n).read_bytes(),hits)
fx=W/'h1c/build/fx'
for n in ['job.sh','job8.sh']+sorted('b/'+q.name for q in (fx/'b').iterdir() if q.is_file())+sorted('b/sa/'+q.name for q in (fx/'b/sa').iterdir() if q.is_file()):
    scan_bytes('derived_kit',n,(fx/n).read_bytes(),hits)
json.dump(hits,open(W/'raw_hits.json','w'),indent=0)
from collections import Counter
print(len(hits));print(Counter((h['surface']) for h in hits))
c=Counter((h['surface'],h['file']) for h in hits);[print(v,k) for k,v in c.most_common(80)]
