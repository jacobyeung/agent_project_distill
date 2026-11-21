import re,sys,io,tarfile,os
src,dst=sys.argv[1],sys.argv[2]
b=open(src,'rb').read()
# find b=bytes.fromhex(...) possibly inside hex-exec'd supervisor
def find(b,depth=0):
    for m in re.finditer(rb"bytes\.fromhex\(['\"]([0-9a-f]+)['\"]\)",b):
        raw=bytes.fromhex(m.group(1).decode())
        pre=b[max(0,m.start()-3):m.start()]
        if pre.endswith(b'b='):
            yield raw
        elif depth<5:
            yield from find(raw,depth+1)
os.makedirs(dst,exist_ok=True)
for i,raw in enumerate(find(b)):
    try:
        t=tarfile.open(fileobj=io.BytesIO(raw))
    except Exception as e:
        print('not tar',i,len(raw));continue
    for m in t.getmembers():
        if m.isfile():
            p=os.path.join(dst,str(i),m.name);os.makedirs(os.path.dirname(p),exist_ok=True)
            open(p,'wb').write(t.extractfile(m).read());print(p)
