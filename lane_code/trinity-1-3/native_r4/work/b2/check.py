import sys,tarfile,hashlib,collections,json
class H:
    def __init__(s,f):s.f=f;s.h=hashlib.sha256();s.n=0
    def read(s,k=-1):
        b=s.f.read(k);s.h.update(b);s.n+=len(b);return b
src=H(sys.stdin.buffer);c=collections.Counter();staging=0
with tarfile.open(fileobj=src,mode='r|') as t:
    for m in t:
        c['dir' if m.isdir() else 'file' if m.isfile() else 'other']+=1
        if '_staging' in m.name:staging+=1
while src.read(1<<20):pass
print(json.dumps(dict(types=c,staging=staging,bytes=src.n,sha256=src.h.hexdigest())))
