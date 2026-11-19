"""Read-only check of changed staging entries and availability of inherited parts."""
import hashlib,json,sys,tarfile
from pathlib import Path

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
class Reader:
 def __init__(self,parts):self.parts=iter(parts);self.f=None;self.h=hashlib.sha256()
 def read(self,n=-1):
  if n<0:n=1<<20
  buf=b''
  while len(buf)<n:
   if self.f is None:
    p=next(self.parts,None)
    if p is None:break
    self.f=open(p,'rb')
   b=self.f.read(n-len(buf))
   if not b:self.f.close();self.f=None;continue
   buf+=b
  self.h.update(buf);return buf

def main(kit,base):
 kit=Path(kit);cur=json.loads((kit/'k/0.json').read_text());sealed=json.loads(Path(base).read_text());known={enc(x) for k in ('tars','extra') for x in sealed.get(k,[])}
 missing=[];verified=[];inherited=[]
 for k in ('tars','extra'):
  for e in cur.get(k,[]):
   for p in e['parts']:
    if not Path(p).is_file():missing.append(p)
   if any(not Path(p).is_file() for p in e['parts']):continue
   if enc(e) in known:inherited.extend(e['parts']);continue
   if k=='extra':
    r=Reader(e['parts'])
    while r.read(1<<20):pass
    if r.h.hexdigest()!=e['sha256']:raise ValueError('extra digest differs')
   else:
    r=Reader(e['parts']);seen={}
    with tarfile.open(fileobj=r,mode='r|') as tf:
     for m in tf:
      if m.name.startswith('/') or '..' in Path(m.name).parts:raise ValueError('unsafe tar path')
      if m.isdir():continue
      if not m.isfile() or m.name not in e['files'] or m.name in seen:raise ValueError('unexpected tar member')
      h=hashlib.sha256()
      f=tf.extractfile(m)
      for b in iter(lambda:f.read(1<<20),b''):h.update(b)
      seen[m.name]=h.hexdigest()
    while r.read(1<<20):pass
    if seen!=e['files'] or r.h.hexdigest()!=e['sha256']:raise ValueError('tar contents or digest differ')
   verified.append(e['parts'])
 return dict(missing=missing,verified=verified,inherited_parts_present=sorted(set(inherited)))

if __name__=="__main__":
 result=main(*sys.argv[1:]);print(json.dumps(result,sort_keys=True));sys.exit(1 if result["missing"] else 0)
